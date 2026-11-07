# MyBible Commentaries Support

Implemented in MyBible for Android v.4.7.0

Revision 2018-06-23

# History of Changes

Revision 2018-06-23

* Clarified/extended conditions of showing commentaries in the modes "Commentaries Relevant to the Current Fragment" and "Commentaries Relevant to the Current Chapter".

Revision 2017-12-16

* For showing of commentaries relevant to the current fragment:  
  * for preceding commentaries, removed the ending part "(to be more precise, if the verse number is visible)".  
  * for concluding commentaries, changed "the last verse" to "any verse".

Revision 2017-12-03

* Initial version, capturing the Oleg's input for MyBible 4.7.0.

# Overview

This specification captures the functionality that MyBible provides to support biblical commentaries.

The purpose of this specification is:

1) To capture the intended functionality, so that it is implemented symmetrically on the Android and iOS platforms

2) To provide a background for users who use commentaries extensively and would like to better understand the intentions and implemented features \- for a more effective use of the tool

Note that MyBible supports biblical commentaries solely as an ancillary tool for studying of the Bible. The Bible text is superior and is to be studied diligently and prayerfully, so that its Author, the Holy Creator God, can send His Holy Spirit to aid the reader in clear understanding of the Scriptures. For that matter, MyBible does not and will not support reading of biblical commentaries as a continuous text \- only as fragments applicable and attached to a particular passage of the Bible.

# Kinds of Commentary Modules

The format of the commentary modules is [documented in the MyBible Modules Format specification](https://docs.google.com/document/d/12rf4Pqy13qhnAW31uKkaWNTBDTtRbNW0s7cM0vcimlA/edit#heading=h.lb9qrxkj3rso).

There are the following kinds of commentary modules.

**Standalone commentaries**. These are modules containing works of scholars who were producing commentaries as such, in a separate printed book. Such commentary modules have distinct abbreviations, usually hinting on the name of the author. For example: Spurg-c, Lapide-c. The suffix "-c" in a commentary module abbreviation is not a necessity but rather some rudiment of the early approach to the commentaries naming; newly produced commentary modules do not have that, e.g. MHWBC.

**Footnotes**. These are commentary modules that are specially marked for MyBibe as footnotes. The nuances here are:

1) Footnote modules have the same abbreviation as the translation modules, and are bundled with translation modules for downloading.

2) A footnote is attached not just to a particular verse, but to a particular place of a particular verse.

3) A footnote module works best with its Bible translation module, because only that translation module has a footnote marker in a needed place.

4) After downloading of a translation module with bundled footnotes, the footnotes module is not shown in the dropdown list of commentary selection in the commentary window (only shown when the user expands that list to see everything).

# Affinity of Commentaries

MyBible distinguishes preceding commentaries and concluding commentaries.

**Preceding commentaries** are those intended by their writer to be read before proceeding to read the Bible text itself.

**Concluding commentaries** are those intended by their writer to help a Bible reader better understand a just read text of the Scriptures.

# Presenting of Commentaries

MyBible has several ways of presenting commentaries:

* **Commentary window**  
  This window shows commentaries from a commentary module explicitly selected by the user for the window. The window shows a single commentary article or several commentary articles one after another, in the defined order of presenting (see "The Order of Presenting Commentaries" below), for one or several verses shown in the Bible window (see "Commentary Window Modes" below).

* **Hyperlinks to commentaries in the Bible text**  
  MyBible allows presenting of commentary articles via hyperlinks in the Bible text. A commentary hyperlink is located before a relevant Bible passage for preceding commentaries, or after a relevant Bible passage for concluding commentaries. A text of a commentary hyperlink is an abbreviation of a corresponding commentary module. A tap on a commentary hyperlink opens a corresponding commentary article in a balloon.

* **Commentaries for a selected verse**  
  MyBible allows showing of all the commentary articles relevant to a single selected verse \- from all the downloaded commentary modules. This is done in a separate, full-screen window. MyBible generates a list where a list item presents all the applicable commentaries from a single particular commentary module, in the defined order of presenting (see "The Order of Presenting Commentaries" below).

## The Order of Presenting Commentaries

When MyBible needs to show several commentary articles in a single window, here is the order of their presenting:

1) Preceding commentaries, starting with more generic, ending with more concrete.

2) Concluding commentaries, starting with more concrete, ending with more generic.

"Generic" and "concrete" above refer to a range of verses that a commentary article covers:

- a commentary article covering a single verse assumed to be most concrete

- a commentary article covering a range of verses is less concrete (the wider the covered range the more generic an article is)

- a commentary for an entire chapter is more generic

- a commentary for an entire book is the most generic.

## Commentary Window Modes

The Commentary window has the following 3 modes of selecting commentaries to be shown:

1) Show commentaries relevant to the current verse.

2) Show commentaries relevant to the current fragment.

3) Show commentaries relevant to the current chapter.

In neither mode there is no special treatment for footnotes.

### Commentaries Relevant to the Current Verse

The following commentary articles are shown in this mode:

1) Commentaries for an entire book, if the current verse is verse 1 of the chapter 1\.

2) Commentaries for an entire chapter, if the current verse is verse 1 of that chapter.

3) Preceding commentaries, for which their verses range starts at the current verse.

4) Concluding commentaries, for which their verses range ends at the current verse.

### Commentaries Relevant to the Current Fragment

The following commentary articles are shown in this mode:

1) Commentaries for an entire book, if the verse 1 of the chapter 1 is shown in the active Bible window.

2) Commentaries for an entire chapter, if the verse 1 of that chapter is shown in the active Bible window.

3) Preceding commentaries, if the first verse of their verses range is shown in the active Bible window.

4) Concluding comments, if any verse of their verses range is shown in the active Bible window.

### Commentaries Relevant to the Current Chapter

1) Commentaries for an entire book, if the current chapter number is 1\.

2) Commentaries for an entire chapter or a set of chapters, if the current chapter number matches the beginning of the commented chapters range.

3) All the commentaries for the current chapter, no matter where the current verse is located within that chapter.

