# MyBible Auto-Hyperlinks Support

Revision 2018-02-24

# History of Changes

Revision 2021-11-30 \- **corresponds to MyBible 5.4.0**

* Added mentioning that a Bible module abbreviation can be enclosed into parentheses.

Revision 2018-02-24 \- **corresponds to MyBible 4.7.3**

* Added support of book abbreviations separated from a chapter or verse number by a comma with no space.

* Taking into account the above change, clarified how a separation character set is selected.

Revision 2017-12-31 \- **corresponds to MyBible 4.7.0**

* Added a section "Recognizing  a book abbreviation".

Revision 2017-12-28

* Added support of concrete Bible modules in hyperlinks.

Revision 2017-12-24

* Initial version, capturing the Oleg's input for MyBible 4.7.0.

# Overview

This specification captures the MyBible's functionality of creating auto-hyperlinks to Bible places in a text typed by the user \- in notes, remarks, descriptions of bookmarks.

The purpose of this specification is:

1) To capture the intended functionality, so that it is implemented symmetrically on the Android and iOS platforms

2) To provide a background for users who create own notes and remarks, mentioning Bible places in them, and would like to have automatically created correct hyperlinks to Bible places in their texts

# Auto-hyperlink definition

Auto-hyperlink is a part of user-entered description or remark in MyBible, which MyBible was able to recognize to be a reference to a Bible place and has made it a tappable hyperlink that leads to the beginning of the recognized Bible position range.

MyBible considers a part of a text to be a reference to a Bible place if it starts with a Bible book abbreviation, followed by a period and/or space, followed by a sequence of numbers, spaces, and separator characters. For example:  
*John 7:53-8:10, 12, 15-17; 9; 11-13; 15-17:1. Mat.2:12, Luk. 15:3-4.*

If a link to a certain Bible module is desired (as opposed to opening a specified Bible place in whatever Bible module is currently opened in the application), simply indicate the Bible module abbreviation before the book name, separated by a space. You can also enclose a module abbreviation into parentheses, if desired.  For example:  
*F35+ John 7:53-8:10, 12, 15-17; 9; 11-13; 15-17:1. See also (BSB'19) Dan 3:12.*

MyBible will recognize abbreviations only of Bible modules already downloaded to the device.

MyBible considers a specified module abbreviation applicable only to the nearest references; its action stops after a word in the text that is not a numerical reference. In the example below the reference to Genesis will be to any currently open Bible module:  
*F35+ John 7:53-8:10, 12, 15-17; 9; 11-13; 15-17:1. See also Gen 11:7; 12-15.*

## Limitations and assumptions

1) Biblical literature uses Bible references which are less formalized compared to the definition above \- they count on understanding of the context by a human reader. For example:

   *see 7: 12 below*

   *verses 7 and 12*

   *vv. 12-14*

   *ch. 12*

   *in chapter 4 of the Gospel of Matthew*  
   *chapters from 12 to 15*

   MyBible does not automatically recognize Bible references like that.

2) In addition to numbers, spaces, and separation characters references to Bible places may contain other characters that are attached to a verse number and make an integral part of a reference:

   *John 7:53b \-* a reference to the second part of a verse

   *Mar 8:12ff, Lk. 18:12+* and so on \- an indication that verses following the specified one are also included in to a referenced range of verses

   Such trailing characters are being considered an integral part of a recognized Bible reference, although they do not affect the actual place where such a reference leads.

# Separation characters

MyBible distinguishes the following categories of separation characters.

- Chapter:Verse

- Verse,Verse

- Chapter;Chapter

- Range Beginning-End

## Chapter:Verse

European Bible publications use the following separation characters for this category:

* period  
* comma  
* colon

after which there is an optional space.

Examples:  
Мт. 2:4  
Mk 7.1  
Mk 7\. 1  
Lk 8,3  
Lk 8, 3

## Verse,Verse

European Bible publications use the following separation characters for this category:

* period  
* comma

after which there is an optional space.

Examples:  
Мt. 2:4, 7  
Mk 7.1,12  
Mk 7\. 1, 10  
Lk 8,3.5  
Lk 8, 3\. 7

## Chapter;Chapter

European Bible publications use the following separation characters:

* semicolon  
* comma \- very rarely, only if it is impossible to interpret the reference in another way

Examples:  
Мт. 7; 12-13; 15\.

## Range Beginning-End

European Bible publications use the following characters to indicate a range, all of which are treated by MyBible in the same way (and referred to simply as "dash"):

* \- (Hyphen-Minus, U+002D)  
* ‒ (Hyphen, U+2010)  
* ‒ (Non-Breaking Hyphen, U+2011)  
* ‒ (Figure Dash, U+2012)  
* – (En Dash, U+2013)  
* — (Em Dash, U+2014)  
* ― (Horizontal Bar, U+2015)

These characters indicate a range of verses or chapters. It is possible that the same reference indicates both a range of chapters and a range of verses. 

Examples:  
Mt. 7:1-2, 7:53-8:11-13, 15-16  
Gen 1-2:3

# Selecting a separation character set

MyBible supports three sets of separation characters meanings listed in the table below.

|  | Chapter:Verse separator | Verse,Verse separator | Chapter;Chapter separator | Range Beginning-End separator |
| :---- | :---: | :---: | :---: | :---: |
| Separation character set 1  | **:** (colon) | **,** (comma) | **;** (semicolon) | \- (any dash) |
| Separation character set 2 | **,** (comma) | **.** (period) | **;** (semicolon) | \- (any dash) |
| Separation character set 3 | **.** (period) | **,** (comma) | **;** (semicolon) | \- (any dash) |

MyBible automatically selects a separation characters set to be used for auto-hyperlinking, based on the first Bible reference found in a user-entered text being processed to create auto-hyperlinks in it:

1) Find the first word in the text, which is a valid Bible book abbreviation, followed by a period and/or space, followed by a number.

2) Check whether a separation character follows the number, and whether another number follows the found separation character (optional spaces around the separation character are ignored).

3) If a separation character is found like described in the previous item, and it is a colon, a comma, or a period, consider it to be the Chapter:Verse separator, and select one of the separation character sets by it from the table above.

# Recognizing a book abbreviation

In Bible modules, MyBible uses book abbreviations that are more or less standardized for the language, and are single words (no spaces or periods in them). However, there usually are several commonly accepted ways of abbreviating Bible books in a particular language. To make abbreviating of books in notes less restrictive for the user, MyBible contains reference data on how particular books can be abbreviated in particular languages (these reference data are collected from popular commentaries and dictionaries in those languages).

The approach to recognizing book abbreviations:

1. In reference data:

   1. Store records containing

      1. book abbreviation

      2. language where it is used

      3. corresponding book number

   2. In case of abbreviations containing spaces, a single space is used in reference data.

2. When checking words from a user-entered text for being a book abbreviation, first check a word by itself, case-sensitive. If it is not a book abbreviation, add the previous word from the left, reduce the user-entered spaces in between to a single space, and check these two words together, still case-sensitive. Keep adding previous words from the left until they make a valid abbreviation, or until you reach a word that already has been included into a recognized reference.

3. Checking whether some string is a book abbreviation:

   1. Check using reference data:

      1. Check whether a specified abbreviation is associated with a single book number, no matter in how many languages. If found, select that book number.

      2. If a specified abbreviation is associated with more than one book number (in several languages), compare the found languages with the MyBible user interface language and then with languages of currently open Bible modules. If a match is found, select a corresponding book number.

   2. If a book abbreviation could not be recognized using reference data, sequentially check all the open Bible modules, starting from a Bible module from the active window, for containing a book with the specified abbreviation, case-sensitive.

# Auto-hyperlinking algorithm

1. Select a separation character set as specified in the previous section.

2. Find the next book abbreviation candidate (this is a potential beginning of a hyperlink): this is a word followed by a space, followed by a number, and a word is a valid book abbreviation, and the number together with the next word after it does not produce a valid book abbreviation (e.g.: Mk. 2 Cor)

3. Check the number after the book abbreviation:

   1. If the book has such a chapter number \- this is a chapter number.

   2. If the book has a single chapter and there is such a verse number \- this is a verse number of the chapter 1\.

   3. Otherwise \- an invalid number, do not start a reference.

4. Keep checking subsequent numbers and separation characters until a word is found that is a not a number and not a separation character.

   1. If the previous number is interpreted as a chapter number:

      1. If the separation character after the previous number is Chapter:Verse, then the current number is a verse number.

      2. If the separation character after the previous number is Range Beginning-End, then the current number is the chapter number, but if the book does not have this chapter number \- the reference ends after the previous number.

      3. If the separation character after the previous number is Chapter;Chapter, then the current number is the chapter number and the reference ends after the previous number. If the book does not have this chapter number \- do not start a new reference.

      4. In other cases the reference ends after the previous number.

   2. If the previous number is interpreted as a verse number:

      1. If a separation character after the previous number was Range Beginning-End:

         1. If a separation character after the current number is Chapter:Verse, then the current number is a chapter number candidate. It is interpreted as a chapter number if it is greater than the previous chapter number, otherwise the reference ends at the previous number.

         2. Else, the current number is a verse number. If a verse with this number does not exist in the previously specified chapter, a reference ends after the previous number.

      2. If a separation character after the previous number is Verse,Verse then the current number is a verse number. The reference ends after the previous number. A new reference starts at the current number, if a verse with this number exists in the previously specified chapter.

      3. If a separation character after the previous number is Chapter;Chapter then the current number is a chapter number. The reference ends after the previous number. A new reference starts at the current number, if a chapter with this number exists in the book.

      4. In other cases the reference ends after the previous number.

# Examples from real publications that shall be auto-hyperlinked

**BHTI**

Mt 3,1-12; Lc 3,1-9.15-17; Jn 1,19-28

Мт 3:1-3:12, Лк 3:1-3:9, Лк 3:15-3:17, Ин 1:19-1:28

**SCH2000**

Mt 3,1-12; Lk 3,1-18; Joh 1,6-8.15-37

Мт 3:1-3:12, Лк 3:1-3:18, Ин 1:6-1:8, Ин 1:15-1:37

**NBS**

Pay attention to spaces before and after “;” 

Mt 3.13-17 ; Lc 3.21-22 ; cf. Jn 1.29-34

**GNB**

Pay attention to the dot and a special kind of dash

(Mt 3.1–12; Lk 3.1–18; Jn 1.19–28) 

(Mt 3.13—4.11; Lk 3.21–22; 4.1–13) 

