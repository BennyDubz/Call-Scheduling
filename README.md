# Doctors/Hospital On-Call Scheduler
### Author: Ben Williams - benjamin.r.williams.25@dartmouth.edu
### First Published: November 29th, 2023
### Last Updated: December 4th, 2023

## The Problem and the Purpose

### Overview of On-Call Scheduling for Doctors

When a doctor is on-call, they can be asked at any point (even at 1AM) to go to the hospital and help someone in the emergency room. The days that a doctor is on call affect their quality of life and need to be factored into how they plan their year. If they have an obligation to be on call one weekend, they cannot go to their child's sporting event or plan a trip - and are overall more limited in what they can do. Or, since doctors are often assigned specific holidays, they cannot travel on those holidays. 

Therefore, it is important for them to know the call schedule ahead of time and for it to be fair as it is a burden that the doctors need to share amongst themselves. These schedules are made to encompass a full year, and are made months in advance to give the doctors adequate time to plan.

### Significance and Implementation

But making a fair call schedule that can handle each doctor's preferences or needs, has quality of life assurances, and can handle specific seniority agreements (some doctors get less call than others), can take a __long time__. These are made a full year in advance, and in speaking to those who have made these schedules before, they often use pencil and paper, __lots of eraser__, and roughly 10 hours of time. 

This program can make these schedules in mere seconds, and the amount work needed to create the input file is much, much less than to create the full schedule. So this program can save these practices countless hours. This program was primarily tailored to my hometown's orthopaedic practice, but is meant to be as generic as possible. 

We frame the call scheduling as a constraint satisfaction problem, and use repeated local search (see `ConstraintSatisfactionProblem.py` and my other [repository](https://github.com/BennyDubz/Constraint_Satisfaction) for more on this) to create a schedule that fulfills all the local (quality of life) and global (fairness) constraints. While the local search that does the bulk of the work is simple, framing the problem and its input into the variables/domains/constraints is what makes the bulk of `CallSchedulingProblem.py`.

### Specific Notes, Rules, and Constraints

- Weekends consist of Friday, Saturday, and Sunday
- If a doctor is on-call on Thursday, they will not be on call that weekend
- If a doctor is on call during a weekend, they will not be on call that next monday (this and previous rule prevent four-day stretches)
- If a doctor is on call during a weekend, they will __not__ be on call for surrounding +/- 2 weekends
- If a doctor is on call during a holiday, they will __not__ be on call for the surrounding +/- 2 weekends
- Every given holiday is assigned one doctor
- If there is not a given weekday schedule or seniority-rules, doctors will all be given an equal amount of weekdays 
- If there are no seniority rules, doctors will all be given the same amount of weekends
- Holidays are given the same weight as weekends, so if there are fewer holidays than doctors, the doctors with no holidays are likely to get an extra weekend

These are implemented in order to create the best and fairest schedule for the doctors.

## Usage

Users can run `create_python.py` through the terminal to create their call schedule, in the following way:

```commandline
python create_python.py start_date end_date input_filepath output_filepath
```

Where the `start_date` and `end_date` are in `mm/dd/yyyy` format.

The file formatting for the `input_file` can be found below in the `File Formatting` section.

The `output_filepath` is __optional__. If it is not provided, the output will go into the current directory.

Example:
```commandline
python create_schedule.py 1/15/2024 1/15/2025 ./testing/definedWeekdays ./results/definedWeekdays_results
```

## Output

The program will output a `.txt` and a `.csv` file in the `output_filepath` directory if it is provided, or in the current directory if it is not provided.

The `.txt` file has all the assignments written week-by-week.

The `.csv` file has schedule, as well as additional information about the holidays, and the number of weekdays/weekends/holidays assigned to each doctor.

## File Formatting

The input file must be specifically formatted in order to create a specific call schedule for your needs. There are several commands, each taking up a line, that you use to break up the text file. Examples can be seen farther in the `README.md`, or in the `testing` folder.

### /defined_weekday_assignment

**This command or /doctor_available_weekdays are required and there can only be one of the two**

If you have this line, then the next several lines must have four doctors per line, specifying which doctor is on that weekday (monday, tuesday, wednesday, thursday). For as many weeks as your schedule is that you would like to loop, that is how many lines you will have after this.

Doctor names must be split up with a comma and a space, as shown.

An example would look like this:
```
/defined_weekday_assignment
Alice, Bob, Charlie, Derrick
Bob, Charlie, Charlie, Charlie
Charlie, Derrick, Charlie, Derrick
Alice, Bob, Charlie, Emily
/next_command (or nothing)
...
```
This would represent a four-week repeating weekday schedule. It begins with the first line, and ends at the last line. In this example, `Emily` would be on call (during the weekdays) only once every four weeks on Thursday, and `Charlie` would be on call every Wednesday.

### /doctor_available_weekdays

**This command or /doctor_weekday_assignment are required and there can only be one of the two**

This line will build the call schedule based on the doctors being available only on specific weekdays (mon/tues/weds/thurs), and not a looping call schedule as in the previous command.

Each line after this (until the next command), must be formatted in the following way:

```
Doctor; DayOfWeek1, DayOfWeek2...
```
With the doctor and the days of the week split by a semicolon and a space, and the days of the week split apart by a comma and a space.

The days of the week must be in this exact list:
```
Monday, Tuesday, Wednesday, Thursday
```

An example is the following:

```
/doctor_available_weekdays
Alice; Monday, Wednesday
Bob; Monday, Wednesday
Charlie; Tuesday, Thursday
Derrick; Tuesday, Thursday
Emily; Monday, Tuesday, Wednesday, Thursday
/next_command (or nothing)
...
```

Here, `Alice` and `Bob` are available on Mondays and Wednesdays, `Charlie` and `Derrick` are available on Tuesdays and Thursdays, and `Emily` is available every day of the week.

**Note:** If there are an uneven amount of people all on the same day, it may be impossible to create a fair schedule! In the above example, if you remove `Bob` and `Emily`, there isn't a way to make a fair schedule for Alice.

### /doctor_unavailable_days

**Note:** This works best if doctors are allowed 1-2 weekends in the year to have off, and you enter all 3-6 dates (3 day weekends remember)

Doctors could have days that they know ahead of time that they are unavailable. If you have this command, you can specify those days. Each line after the command must have the following formatting:
```
Doctor; mm/dd/yyyy, mm/dd/yyyy, ..., mm/dd/yyyy
```
Again, with the semicolon and space splitting the doctor/days apart and the days being separated by a comma and space.

An example:

```
/doctor_unavailable_days
Alice; 12/1/2023, 12/2/2023, 12/3/2023
Bob; 12/25/2023
```
In this case, Alice cannot be assigned on that weekend, and Bob will not be given the Christmas holiday (if you have Christams in your holiday list, see below)

### /holiday_dates

This allows you to specify specific holidays for doctors to be assigned. Each line has dates, separated by a comma and a space

An example:
```
/holiday_dates
5/24/2024, 5/25/2024, 5/26/2024, 5/27/2024
7/4/2024
8/30/2024, 8/31/2024, 9/1/2024, 9/2/2024
11/28/2024
12/25/2024
12/31/2024, 1/1/2025
```

In this example, Memorial Day Weekend, the Fourth of July, Labor Day Weekend, Thanksgiving, Christmas, and NYE/New Years are all given a line.

### /max_weekends and /max_weekdays

**Note:** `/max_weekdays` can only be used if you are using the `/doctor_weekday_availability` metric to build the schedule.

These commands allow you to specify doctors having a maximum number of weekdays or weekends assigned to them. This allows for the user to have some seniority implemented, if they want some doctors to have fewer weekdays or weekends than others.

An example is here:
```
/max_weekends
Alice; 5
Bob; 6
```
The doctors and the numbers are split by a semicolon and a space. This means that Alice will only be assigned 5 weekends, and Bob will only be assigned 6 weekends. If done for a full year, this is fewer weekends than the other doctors.

The same format is used for `/max_weekdays`

### /additional_doctors

This allows you to have additional doctors to be put in on weekends and holidays, but are not mentioned anywhere else. Doctors that are used in any other command do not need to be put here.

Format - one doctor per line. Example:
```
/additional_doctors
George
Nathan
Julia
```

These three doctors will be added onto the weekend and holiday rotations.

## Examples

Full examples can be seen in the `testing` folder, however, here is one:

```
/doctor_weekday_assignment
Alice, Bob, Charlie, Derrick
Emily, Bob, Charlie, Fred
Alice, Bob, Charlie, Derrick
Emily, Emily, Fred, Fred
/doctor_unavailable_days
Alice; 12/25/2024
Bob; 2/2/2024, 2/3/2024, 2/4/2024,
Charlie; 3/22/2024, 3/23/2024, 3/24/2024
Emily; 6/21/2024, 6/22/2024, 6/23/2024
/holiday_dates
5/24/2024, 5/25/2024, 5/26/2024, 5/27/2024
7/4/2024
8/30/2024, 8/31/2024, 9/1/2024, 9/2/2024
11/28/2024
12/25/2024
12/31/2024, 1/1/2025
/max_weekends
Emily; 6
/additional_doctors
George
```

This would be a valid file that has a looping four-week schedule. Some doctors have days that they are unavailable. The same holidays used above are used here. Emily has seniority, and only can be assigned 6 weekends, and George can help fill in for weekends and a holiday.



