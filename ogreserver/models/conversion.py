from __future__ import absolute_import
from __future__ import unicode_literals

import os
import shutil
import subprocess

from flask import current_app as app

from ..exceptions import ConversionFailedError, EbookNotFoundOnS3Error
from ..stores import ebooks as ebook_store
from ..utils.ebooks import compute_md5, id_generator
from ..utils.generic import make_temp_directory
from ..utils.s3 import connect_s3


class Conversion:
    def __init__(self, config):
        self.config = config


    def search(self, limit=None):
        """
        Search for ebooks which are missing the key formats epub & mobi
        """
        for dest_fmt in self.config['EBOOK_FORMATS']:
            # load all Versions which are missing format dest_fmt
            versions = ebook_store.find_missing_formats(dest_fmt, limit=None)

            for version in versions:
                # ensure source ebook has been uploaded
                if version.source_format.uploaded is True:
                    # convert source to dest_fmt
                    app.signals['convert-ebook'].send(
                        self,
                        ebook_id=version.ebook_id,
                        version_id=version.id,
                        original_filename=version.source_format.s3_filename,
                        dest_fmt=dest_fmt
                    )


    def convert(self, ebook_id, version, original_filename, dest_fmt):
        """
        Convert an ebook to both mobi & epub based on which is missing

        ebook_id (str):             Ebook's PK
        version (Version obj):
        original_filename (str):    Filename on S3 of source book uploaded to OGRE
        dest_fmt (str):             Target format to convert to
        """
        with make_temp_directory() as temp_dir:
            # generate a temp filename for the output ebook
            temp_filepath = os.path.join(temp_dir, '{}.{}'.format(id_generator(), dest_fmt))

            # download the original book from S3
            s3 = connect_s3(self.config)
            bucket = s3.get_bucket(self.config['EBOOK_S3_BUCKET'].format(app.config['env']))
            k = bucket.get_key(original_filename)
            if k is None:
                raise EbookNotFoundOnS3Error

            original_filename = os.path.join(temp_dir, original_filename)
            k.get_contents_to_filename(original_filename)

            # call ebook-convert, ENV is inherited from celery worker process (see supervisord conf)
            proc = subprocess.Popen(
                ['/usr/bin/env', '/usr/bin/ebook-convert', original_filename, temp_filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # get raw bytes and interpret and UTF8
            out_bytes, err_bytes = proc.communicate()
            out = out_bytes.decode('utf8')

            if len(err_bytes) > 0:
                raise ConversionFailedError(err_bytes.decode('utf8'))
            elif '{} output written to'.format(dest_fmt.upper()) not in out:
                raise ConversionFailedError(out)

            # write metdata to ebook
            file_hash = self._ebook_write_metadata(ebook_id, temp_filepath, dest_fmt)

            # move converted ebook to uploads dir, where celery task can push it to S3
            dest_path = os.path.join(self.config['UPLOADED_EBOOKS_DEST'], '{}.{}'.format(file_hash, dest_fmt))

            try:
                shutil.move(temp_filepath, dest_path)
            except subprocess.CalledProcessError as e:
                raise ConversionFailedError(inner_excp=e)

        # add newly created format to store
        ebook_store.create_format(version, file_hash, dest_fmt)

        # signal celery to store on S3
        app.signals['upload-ebook'].send(
            self,
            ebook_id=ebook_id,
            filename=dest_path,
            file_hash=file_hash,
            fmt=dest_fmt,
            username='ogrebot'
        )


    def _ebook_write_metadata(self, ebook_id, filepath, fmt):
        """
        Write metadata to a file from the OGRE DB

        ebook_id (uuid):        Ebook's PK
        filepath (str):         Path to the file
        fmt (str):              File format
        """
        # load the ebook object
        ebook = ebook_store.load_ebook(ebook_id)

        with make_temp_directory() as temp_dir:
            # copy the ebook to a temp file
            temp_file_path = '{}.{}'.format(os.path.join(temp_dir, id_generator()), fmt)
            shutil.copy(filepath, temp_file_path)

            # write the OGRE id into the ebook's metadata
            if fmt == 'epub':
                Conversion._write_metadata_identifier(ebook, temp_file_path)
            else:
                Conversion._write_metadata_tags(ebook, temp_file_path)

            # calculate new MD5 after updating metadata
            new_hash = compute_md5(temp_file_path)[0]

            # move file back into place
            shutil.copy(temp_file_path, filepath)
            return new_hash

    @staticmethod
    def _write_metadata_tags(ebook, temp_file_path):
        # append ogre's ebook_id to the ebook's comma-separated tags field
        # as Amazon formats don't support identifiers in metadata
        if ebook.raw_tags is not None and len(ebook.raw_tags) > 0:
            new_tags = 'ogre_id={}, {}'.format(ebook.id, ebook.raw_tags)
        else:
            new_tags = 'ogre_id={}'.format(ebook.id)

        # write ogre_id to --tags
        subprocess.check_output(
            '/usr/bin/ebook-meta {} --tags {}'.format(temp_file_path, new_tags),
            stderr=subprocess.STDOUT,
            shell=True
        )

    @staticmethod
    def _write_metadata_identifier(ebook, temp_file_path):
        # write ogre_id to identifier metadata
        subprocess.check_output(
            '/usr/bin/ebook-meta {} --identifier ogre_id:{}'.format(temp_file_path, ebook.id),
            stderr=subprocess.STDOUT,
            shell=True
        )
