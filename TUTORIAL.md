# Getting started with Assigner

This document will walk you through the workflow for setting up a class with Assigner and creating, assigning, and fetching student homework.

We'll assume you have installed Assigner using `pip install assigner` or `pip3 install assigner`.
(If you don't have adminstrator access on your machine, you can run `pip install --user assigner` and put `~/.local/bin` in your `$PATH` instead.)

## Setting up a new class

The first thing you should do when setting Assigner up for a course is to create a directory to hold assignment descriptions and student submissions.

### Configuring Assigner (`assigner init`)

Assigner needs to know various bits of information about GitLab and your course to do its job.
It stores this information in a file named `_config.yml` in your current directory.
For an example of what this file ought to contain, see `_config.example.yml` in the Assigner git repository.

**Note:** Your `_config.yml` will contain at least one access token; therefore, you should be careful that others are not able to read your `_config.yml`.
Treat it as you would a file containing a password or your Social Security Number.

Rather than making a config file by hand, Assigner has a command that will interactively prompt you for the required information.
So, `cd` into the directory you've made for the course, then execute `assigner init`.
It will prompt you for the following information:

1. GitLab host to use.
    The default choice is `gitlab.com`, but if you plan to use a version of GitLab hosted by, say, your university, you should enter that host here instead.
2. GitLab access token.
    You must create one of these in your GitLab user profile; Assigner will generate a URL that should link you to the page to do that.
    Assigner uses this token to authenticate with GitLab so you don't have to enter your password constantly.
3. The year and semester ('FS' for fall semester, 'SP' for spring semester, or 'SS' for summer semester).
    Assigner will do its best to guess what semester and year it is for you.
    This information is used to name student repositories so that students can easily sort and organize their various assignments.
4. GitLab group to create assignments under.
    We recommend making a group on GitLab for each course; the default value shows the naming scheme we recommend.
    Right now, Assigner does not create this group for you, so you will need to do that yourself.
    **Do not** add students to this group; if you do, they will be able to see all student submissions!
    If you like, you may add graders and TAs to the group.
    Note that you'll need to be an Owner of the group in order to use all of Assigner's features.
5. Canvas information. This is optional; you should enter this information if you want to import your class roster from Canvas.
    We recommend this, as it is the most straightforward way to import a class roster.
    If you enter `y` here, Assigner will prompt you for:
    1. The Canvas server to use, typically of the form `<institution name>.instructure.com`.
    2. A Canvas API access token. As with GitLab, you must generate one of these yourself. Assigner provides a URL to the page where you can do that.

In addition, you will need to [configure GitLab with your SSH public key](https://docs.gitlab.com/ce/ssh/README.html).

### Adding students to the roster

Once you have set up Assigner for your course, you should add students to your course roster so that you can assign them homework!
There are three possible ways to do this:

1. Import a roster from Canvas.
2. Import a roster from a PeopleSoft-generated CSV file (e.g., from Joe'SS).
3. Enter students manually.

When importing students, you may receive a warning that a student does not have a GitLab account.
What this means, most likely, is that the student has not logged in to GitLab yet.
Do not worry too much about this; Assigner will attempt to fetch the GitLab account information of students that are missing it whenever possible.
You should instruct your students to log in to GitLab at least once so that you can grant them access to their homework repositories.
Once a student logs in at least once, Assigner will automatically fill in their account information.

#### Importing from Canvas (`assigner canvas list` / `assigner canvas import`)

The simplest way to add students to your Assigner course roster is to import them from Canvas.

1. Run `assigner canvas list` to list the courses on Canvas where you are a teacher, TA, or grader.
    Make a note of the ID of the course whose roster you want to import.
    **Note**: Assigner currently only shows published Canvas courses.
2. Run `assigner canvas import <course ID> <section letter>`. Use the course ID from the previous step.
    You can import several sections into the same roster by specifying different section letters.

#### Importing from PeopleSoft (`assigner import`)

If your institution uses PeopleSoft to manage students and class rosters, you can import those rosters into Assigner as well.
This process is a little hacky, so if you run into trouble, please [report a bug](https://github.com/redkyn/assigner/issues)!

1. Navigate to your course roster on PeopleSoft.
2. In the 'Enrolled Students' table header, there is a button that looks like a grid with a red arrow in the top left corner.
    If you hover your mouse cursor over the button, it should display 'Download Enrolled Students Table to Excel'.
    Click this button and save the resulting file somewhere.
3. Open the file you downloaded in step 2 in Excel or LibreOffice and save it as a CSV.
    (You may notice that the name of the file you downloaded already ends in `.csv`.
     This is a convenient lie; PeopleSoft actually exports an HTML table and relies on Excel to detect and import this correctly.
     Assigner expects an actual honest-to-goodness CSV file, so you need to use Excel to generate one.)
4. Run `assigner import <path to file generated in step #3> <section letter>`.
    You can import several sections into the same roster by specifying different section letters.

#### Entering student information manually

You can manage your roster manually with the `assigner roster` command and its subcommands.

To add a new student, run `assigner roster add <student name> <student GitLab username> <section letter>`.
(Typically the student's GitLab username will match their university email.)

To list the students in your course, run `assigner roster list`.
If you only want to list one section, say, section B, you can do that by running `assigner roster list --section B`.

Lastly, you can remove students by running `assigner roster remove <student GitLab username>`.

## The assignment workflow

Once you have set Assigner up for your class, you can use it to make and assign homeworks and to fetch submissions from your students.

Each assignment has a **template repository** that you add assignment materials to.
The template repository is then copied to **student repositories**, one per student.

This section will walk you through making a new assignment named 'hw1' and performing various actions on it.

### Creating a new template repository

To create the template repository for the new assignment, run `assigner new hw1`.
Assigner will create a new repository named 'hw1' in the GitLab group specified in `_config.yml`.
It then will print out both an HTTPS and an SSH URL that you can use to view this repo in the GitLab UI or to clone a local copy.

Now you should add any materials your students need to complete the assignment to this repo.
At the bare minimum, you should create a `README` file with a link to where the students can view the assignment directions.
Commit your changes and push them to GitLab.

### Creating student repositories

Once you have created a template repo, you can make student repos from it by running `assigner assign hw1`.
This step *only* creates the repositories; it does not add the students to them.
You should open GitLab and verify that the students' repo contents look correct.
Each repository should be named something along the lines of `2017-FS-A-hw1-bob123`.

By default, `assigner assign` copies only the `master` branch from the template repo.
Typically, this is what you want.
If you wish to upload different branches, you can pass the `--branch` flag and list the branches you want to push.
For example, let's say that in addition to the `master` branch, you want to provide your students with a copy of the `devel` branch from the template repo.
To do so, you'd run `assigner assign hw1 --branch master devel`.

### Opening the assignment to students

Now that you have created the student repos, you can add your students to them so they can work on the assignment!
To do so, run `assigner open hw1`.
This will grant each student [developer](http://docs.gitlab.com/ce/user/permissions.html) permissions on their associated repository.

If some students have yet to log in to GitLab, you may see some warnings.
Remind the students to log in to GitLab so they have a user account.
Once they have, you can re-run `assigner open hw1` to grant them access to their repos.

### Checking up on student progress

You may want to check from time to time to see if students have made progress on their assignment.
To do this, run `assigner status hw1`.
It will print a table of each student in the roster along with the author, time, and hash of the latest commit made to their student repo.

### Fetching student submissions

Once the submission deadline for an assignment has passed, you can clone each student repo using `assigner get hw1`.
Assigner will create a directory named 'hw1' in the current directory, then clone each student repo into a subdirectory of that directory.
You can then inspect and grade the assignments however you like.

If you want to collect late submissions, you can re-run `assigner get hw1`.
It will fetch changes for each existing repository and clone any nonexisting repositores.

If you encounter 'Connection reset by peer' errors when cloning, run, say, `assigner get hw1 --attempts=10` to have Assigner try cloning 10 times before giving up.

(Assigner doesn't have plans for any grading features;
however, if you are interested in automated grading, check out its sister project, [grader](https://github.com/redkyn/grader).)

### Committing and pushing changes to student repositories

You can make and push commits to student repositories after they have been created with `assigner assign` by using `assigner commit` and `assigner push`.
These commands should be used carefully!
It is quite possible to give your students merge conflicts if they are still making commits to their repository while you are making changes.
We recommend using this feature very carefully if students are intended to continue working in their repos after you push your commits.

We recommend using the following workflow with `commit` and `push`:

1. Lock student repositories with `assigner lock`.
    This will prevent students from pushing to their repositories before you push your changes.
2. Clone or pull local copies of their repositories using `assigner get`.
3. Make the changes you require in each repository.
4. Commit your changes.
    `assigner commit assignment-name "my commit message"` behaves effectively like executing `git checkout master; git commit -am "my commit message` in each student repository.
    Add new files by specifying their names after the `-a` flag; remove files by specifying their names after the `-r` flag.

    To add all untracked files in each student's repository, run `assigner commit assignment-name "commit message" -a "*"`.

    As a more extended example, the command 
    ```
    assigner commit assignment-name "my commit message" -a newfile.txt -r junk.dat -u --branch devel
    ```
    corresponds to executing the following commands in each repository:
    ```
    git checkout devel
    git add newfile.txt
    git rm junk.dat
    git commit --all --message="my commit message"
    ```
5. Push your commits with `assigner push`.
    If you did not lock the students' repositories, Assigner will print an error and exit.
    We recommend locking their repositories, then updating your local copies with `assigner get` before pushing.
    However, if you are absolutely sure of what you are doing, you can override this check with the `--push-unlocked` flag.

### Student repository management

If you wish to prevent students from submitting after the deadline, you may lock their repositories by running `assigner lock hw1`.
This changes each student's access level to reporter, so they may view their repository but not push further changes to it.
To re-grant them developer access, run `assigner unlock hw1`.

By default, the branches of each student repo created by Assigner are protected; students cannot force-push to it.
Typically this is what you want; however, should you want to change that, you may unprotect (or re-protect) branches using `assigner protect`.
For example, to unprotect the `master` branch, run `assigner unprotect hw1`.
If you want to protect a branch named `devel`, run `assigner protect hw1 --branch devel`.
