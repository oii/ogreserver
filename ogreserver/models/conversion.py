from __future__ import absolute_import
from __future__ import unicode_literals

import os
import shutil
import subprocess

from ..exceptions import ConversionFailedError, EbookNotFoundOnS3Error
from ..utils import compute_md5, connect_s3, id_generator, make_temp_directory


class Conversion:
    def __init__(self, config, datastore, flask_app):
        self.config = config
        self.datastore = datastore
        self.flask_app = flask_app


    def search(self):
        """
        Search for ebooks which are missing the key formats epub & mobi
        """
        for dest_fmt in self.config['EBOOK_FORMATS']:
            # load all versions missing dest_fmt
            versions = self.datastore.find_missing_formats(dest_fmt)

            for version_id, formats in versions.items():
                # ebook_id & original format are same for all versions
                ebook_id = formats[0]['ebook_id']
                original_format = formats[0]['original_format']

                # get the filehash of the original uploaded ebook
                original_filehash = next((f['file_hash'] for f in formats if original_format == f['format']), None)

                # ensure source ebook has been uploaded
                if self.datastore.get_uploaded(original_filehash):
                    # generate the filename of the original uploaded ebook (the file's name on S3)
                    original_filename = self.datastore.generate_filename(original_filehash)

                    # convert source format to required formats
                    self.flask_app.signals['convert-ebook'].send(
                        self,
                        ebook_id=ebook_id,
                        version_id=version_id,
                        original_filename=original_filename,
                        dest_fmt=dest_fmt
                    )


    def convert(self, ebook_id, version_id, original_filename, dest_fmt):
        """
        Convert an ebook to both mobi & epub based on which is missing

        ebook_id (int):             Ebook's PK
        version_id (str):           PK of this version
        original_filename (str):    Filename on S3 of source book uploaded to OGRE
        dest_fmt (str):             Target format to convert to
        """
        # generate a temp filename for the output ebook
        output_filename = os.path.join(
            self.config['UPLOADED_EBOOKS_DEST'], '{}.{}'.format(
                id_generator(), dest_fmt
            )
        )

        # ensure directory exists
        if not os.path.exists(self.config['UPLOADED_EBOOKS_DEST']):
            os.makedirs(self.config['UPLOADED_EBOOKS_DEST'])

        # download the original book from S3
        s3 = connect_s3(self.datastore.config)
        bucket = s3.get_bucket(self.config['S3_BUCKET'])
        k = bucket.get_key(original_filename)
        if k is None:
            raise EbookNotFoundOnS3Error
        original_filename = os.path.join(
            self.config['UPLOADED_EBOOKS_DEST'], original_filename
        )
        k.get_contents_to_filename(original_filename)

        # call ebook-convert, ENV is inherited from celery worker process (see supervisord conf)
        proc = subprocess.Popen(
            ['/usr/bin/env', '/usr/bin/ebook-convert', original_filename, output_filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = proc.communicate()

        if len(err) > 0:
            raise ConversionFailedError(err)
        elif '{} output written to'.format(dest_fmt.upper()) not in out:
            raise ConversionFailedError(out)

        # calculate file hash of newly created book
        md5_tup = compute_md5(output_filename)

        # write metdata to ebook
        self.ebook_write_metadata(ebook_id, md5_tup[0], output_filename, dest_fmt)

        try:
            # move newly decrypted book to its final filename; the new file hash
            subprocess.check_call("mv '{}' '{}'".format(
                output_filename,
                os.path.join(
                    self.config['UPLOADED_EBOOKS_DEST'],
                    '{}.{}'.format(md5_tup[0], dest_fmt)
                ),
                shell=True
            ))
        except subprocess.CalledProcessError as e:
            raise ConversionFailedError(inner_excp=e)

        # add newly created format to datastore
        self.datastore._create_new_format(version_id, md5_tup[0], dest_fmt)

        # signal celery to store on S3
        self.flask_app.signals['store-ebook'].send(
            self,
            ebook_id=ebook_id,
            file_hash=md5_tup[0],
            fmt=dest_fmt,
            username='ogrebot'
        )


    def ebook_write_metadata(self, ebook_id, file_hash, filepath, fmt):
        """
        Write metadata to a file from the OGRE DB

        ebook_id (int):         Ebook's PK
        file_hash (str):        File's hash
        filepath (str):         Path to the file
        fmt (str):              File format
        """
        # load the ebook object
        ebook = self.datastore.load_ebook(ebook_id)

        with make_temp_directory() as temp_dir:
            # copy the ebook to a temp file
            tmp_name = '{}{}'.format(os.path.join(temp_dir, id_generator()), fmt)
            shutil.copy(filepath, tmp_name)

            if fmt[1:] in self.config['MOBI_FORMATS']:
                # append ogre's ebook_id to the ebook's comma-separated tags field
                if ebook['raw_tags'] is not None and len(ebook['raw_tags']) > 0:
                    new_tags = 'ogre_id={}, {}'.format(ebook['ebook_id'], ebook['raw_tags'])
                else:
                    new_tags = 'ogre_id={}'.format(ebook['ebook_id'])

                # write ogre_id to --tags
                subprocess.check_output(
                    '/usr/bin/ebook-meta {} --tags {}'.format(tmp_name, new_tags),
                    stderr=subprocess.STDOUT,
                    shell=True
                )
            else:
                # write ogre_id to --identifier
                subprocess.check_output(
                    '/usr/bin/ebook-meta {} --identifier ogre_id:{}'.format(tmp_name, ebook_id),
                    stderr=subprocess.STDOUT,
                    shell=True
                )

            # calculate new MD5 after updating metadata
            new_hash = compute_md5(tmp_name)[0]

            # update the self.datastore
            self.datastore.update_ebook_hash(file_hash, new_hash)

            # move file back into place
            shutil.copy(tmp_name, filepath)
            return new_hash
