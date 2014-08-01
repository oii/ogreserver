Title: Adobe Digital Editions
Date: 2014-08-01
Status: published
Summary: Help on handling ebooks bought with vendors using Adobe Digital Editions


### Intro

Adobe Digital Editions (ADE)[^1] is a third party DRM system which Adobe lease out to ebook vendors. A single login managed by Adobe called your "Adobe ID" allows you to access/decrypt books bought from any of the ebook stores in the program[^2].

Notable sites which use ADE for their DRM include (with links to their help pages):

 - Kobo book store[^3]
 - Book Depository (which no longer operates!)


### Working with O.G.R.E.

Using Digital Editions is with O.G.R.E. to free your books is relatively straight forward - if you're already setup with ADE and have your ebooks downloaded, you probably don't need to do anything further.

Installing and setting up ADE:

 1. [Download](http://www.adobe.com/products/digital-editions/download.html) and install ADE on your computer.
 2. Authorise your computer by logging in with your Adobe ID.

Downloading your DRM-mangled ebooks will vary from site to site. Using Kobo's store as an example:

 1. Goto the Kobo store and log in.
 2. Click on "My Library" in the header.
 3. You're presented with a list of purchased books, each with a button similar to "ABODE DRM EPUB"
 4. Clicking the button will download and open in the book in ADE.
 5. If it doesn't open in ADE automatically, find the `.acsm` file just downloaded and double-click to open in ADE.

Now you can run `ogreclient` and it will find and decrypt your ADE books :D


### Switching Authorisation

ADE only supports a single authorised Adobe ID at any time. You can deauthorise your current installation by pressing `Cmd+Shift+D`, which allows you to reauthorise with a different Adobe ID.


[^1]: [Wikipedia](http://en.wikipedia.org/wiki/Adobe_Digital_Editions)

[^2]: [Adobe Accounts](https://accounts.adobe.com/)

[^3]: [Kobo ADE](http://www.kobobooks.com/ade)
