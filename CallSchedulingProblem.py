import math
import sys
import copy

from ConstraintSatisfactionProblem import ConstraintSatisfactionProblem
import calendar
import datetime
import random

# Author: Ben Williams '25, benjamin.r.williams.25@dartmouth.edu
# Date: November 5th, 2023


class CallSchedulingProblem(ConstraintSatisfactionProblem):

    # Takes datetime objects start_date and end_date, and a call_file with all the doctor-specific info
    def __init__(self, start_date, end_date, call_file):
        self.start_date = start_date
        self.end_date = end_date
        self.holidays = set()
        self.holiday_indices = []
        self.doctors = set()
        self.doc_unavailable_days = dict()
        self.max_weekends = dict()
        self.max_weekdays = dict()

        # If the weekday schedule is explicitly defined, then we do not randomly assign weekdays, but rather use this
        #   list. This list is built in the parse_call_file method, if applicable.
        self.weekday_schedule = []
        # Otherwise, we will use this dictionary to assign weekdays
        # Only relevant weekdays, Fri/Sat/Sun are one block
        self.doc_available_weekdays = {"Monday": [], "Tuesday": [], "Wednesday": [], "Thursday": []}

        self.parse_call_file_wrapper(call_file)

        # Initialize values in dictionaries that were not completely filled out
        for doc in self.doctors:
            if doc not in self.doc_unavailable_days.keys():
                self.doc_unavailable_days[doc] = []

        # Variables --> Every weekday, every weekend, and every holiday
        self.variables = self.create_variable_dates()

        # Domains --> Doctors available that day, weekend, or holiday
        self.domains = self.get_domains()

        # Constraints --> Rules:
        #   Spread out holidays and weekends. If on one weekend/holiday, you cannot be on for another weekend
        #       in the near future/past
        #   No back to back weekdays/weekends. If on call Monday, cannot be on call the weekend right before. Likewise,
        #       if on call Thursday, cannot be on call the weekend immediately after (no thurs-fri-sat-sun)
        #       This is not considered
        self.constraints = self.get_constraints()

        # Global constraints --> Rules (handled in the solver):
        #   Every day needs exactly one doctor. Is handled in the solver.
        #   The schedule should be fair. Everyone should have roughly the same amount of weekends and holidays.
        #       If the weekday_schedule is undefined, they should also have the same amount of weekends

        super().__init__(self.variables, self.domains, self.constraints)

    # Performs multiple local searches to ensure that the doctors have evenly distributed days
    # Restarts when necessary, since if a solution is not found quickly - we are likely stuck in local minima.
    def solve_for_call_schedule(self, print_info=False):
        # Our first assignment
        if self.weekday_schedule:
            initial_assignment = self.get_initial_assignment()
            # schedule = self.backtracking_solver(assignment=initial_assignment)
            schedule = self.local_search(1000, assignment=initial_assignment)[0]
        else:
            schedule = self.local_search(1000)[0]

        original_domains = copy.deepcopy(self.domains)

        # Continue until local search succeeds
        num_attempts = 1
        while not schedule and num_attempts < 100:
            if print_info:
                print("local search attempt", num_attempts)

            schedule = self.local_search(1000)[0]
            num_attempts += 1

        if num_attempts == 100:
            print("Call scheduling potentially impossible", file=sys.stderr)
            return None

        if print_info:
            doc_weekdays, doc_weekends, doc_holidays = self.get_doc_days_assigned(schedule)
            print(f"Original assignment: \n", doc_weekdays, "\n", doc_weekends, "\n", doc_holidays)

        attempts = 1
        # Continue to adjust the schedule until it is fair
        while self.remove_unfair_assignments(schedule):

            if print_info:
                doc_weekdays, doc_weekends, doc_holidays = self.get_doc_days_assigned(schedule)
                print(f"After removing parts of schedule at {attempts} attempts:\nWeekday totals:", doc_weekdays,
                      "\nWeekend totals:", doc_weekends, "\nHoliday totals:", doc_holidays)
            attempts += 1

            if attempts % 100 == 0 and attempts > 0:
                if print_info:
                    print("Likely faster to restart")
                self.domains = copy.deepcopy(original_domains)
                schedule = self.local_search(1000)[0]
                while not schedule:
                    schedule = self.local_search(1000)[0]

            inside_attempts = 1
            new_schedule = self.local_search(200, assignment=schedule)[0]
            while not new_schedule:
                # This is probably impossible to solve from here, so back up to the beginning
                if inside_attempts > 5:
                    if print_info:
                        print("Locally impossible schedule. Backing out and trying again.")
                        self.domains = copy.deepcopy(original_domains)
                    new_schedule = self.local_search(1000)[0]
                    while not new_schedule:
                        new_schedule = self.local_search(1000)[0]
                    break
                new_schedule = self.local_search(200, assignment=schedule)[0]
                inside_attempts += 1

            schedule = new_schedule

            if print_info:
                doc_weekdays, doc_weekends, doc_holidays = self.get_doc_days_assigned(schedule)
                print(f"Status at {attempts} attempts:\nWeekday totals:", doc_weekdays, "\nWeekend totals:",
                      doc_weekends, "\nHoliday totals:", doc_holidays)
                print("----------")

        # No need to deep copy as we are not modifying the domains anymore
        self.domains = original_domains
        return schedule

    # Returns True if the assignment has been altered, False otherwise
    # Ensures all doctors have an equal number of weekdays and weekends,
    #   and that the max_weekdays and max_weekends rules (if given) are followed
    def remove_unfair_assignments(self, assignment):
        doc_weekdays, doc_weekends, doc_holidays = self.get_doc_days_assigned(assignment)

        # If the differences are small and there are no max days violations, we don't need to change the schedule
        change_weekends = False
        change_weekdays = False

        # Measure the fairness for weekdays
        min_num_weekdays = math.inf
        max_num_weekdays = 0
        for doc in doc_weekdays.keys():
            if doc_weekdays[doc] < min_num_weekdays:
                if doc in self.max_weekdays.keys() and doc_weekdays[doc] == self.max_weekdays[doc]:
                    continue
                min_num_weekdays = doc_weekdays[doc]
            if doc_weekdays[doc] > max_num_weekdays:
                max_num_weekdays = doc_weekdays[doc]

            if doc in self.max_weekdays.keys() and doc_weekdays[doc] > self.max_weekdays[doc]:
                change_weekdays = True

        # Measure the fairness for weekends
        min_num_weekends = math.inf
        max_num_weekends = 0
        for doc in doc_weekends.keys():
            if doc_weekends[doc] + doc_holidays[doc] < min_num_weekends:
                if doc in self.max_weekends.keys() and doc_weekends[doc] == self.max_weekends[doc]:
                    continue
                min_num_weekends = doc_weekends[doc] + doc_holidays[doc]
            if doc_weekends[doc] + doc_holidays[doc] > max_num_weekends:
                max_num_weekends = doc_weekends[doc] + doc_holidays[doc]

            if doc in self.max_weekends.keys() and doc_weekdays[doc] > self.max_weekends[doc]:
                change_weekends = True

        if max_num_weekdays - min_num_weekdays > 1:
            change_weekdays = True
        if max_num_weekends - min_num_weekends > 1:
            change_weekends = True

        # If we have an explicitly defined weekday schedule, do not change the weekdays!
        if self.weekday_schedule:
            change_weekdays = False

        if not change_weekdays and not change_weekends:
            return False

        rand_indices = [i for i in range(len(assignment))]
        random.shuffle(rand_indices)
        for index in rand_indices:
            # If this is a weekend or holiday assignment
            if type(self.variables[index]) == tuple:

                # Do not change holidays
                if self.variables[index] in self.holidays:
                    continue

                # If we are going to change the weekend assignments
                if change_weekends:
                    removed = False
                    # If the doctor has too many weekends, wipe the assignment
                    if assignment[index] in self.max_weekends.keys():
                        if doc_weekends[assignment[index]] > self.max_weekends[assignment[index]]:
                            doc_weekends[assignment[index]] -= 1
                            assignment[index] = None
                            removed = True
                    if not removed and doc_weekends[assignment[index]] > min_num_weekends:
                        doc_weekends[assignment[index]] -= 1
                        assignment[index] = None

            else:
                # If we are going to change the weekday assignments
                if change_weekdays:
                    removed = False
                    # If the doctor has too many weekdays, wipe the assignment
                    if assignment[index] in self.max_weekdays.keys():
                        if doc_weekdays[assignment[index]] > self.max_weekdays[assignment[index]]:
                            doc_weekdays[assignment[index]] -= 1
                            assignment[index] = None
                            removed = True
                    if not removed and doc_weekdays[assignment[index]] > min_num_weekdays:
                        doc_weekdays[assignment[index]] -= 1
                        assignment[index] = None

        # Lock the domains to avoid re-adding weekdays or weekdays to doctors who have reached their max
        # This prevents the algorithm from continuously adding to these doctors, slowing it down
        # It is a greedy decision that has worked out in practice. But the original domains are kept in case it fails.
        for doc in self.max_weekdays.keys():
            if doc_weekdays[doc] == self.max_weekdays[doc]:
                for i in range(len(self.domains)):
                    # Ignore weekdays and holidays
                    if type(self.variables[i]) == tuple or self.variables[i] in self.holidays:
                        continue
                    if doc in self.domains[i]:
                        self.domains[i].remove(doc)
        for doc in self.max_weekends.keys():
            if doc_weekends[doc] == self.max_weekends[doc]:
                for i in range(len(self.domains)):
                    if type(self.variables[i]) != tuple:
                        continue
                    if doc in self.domains[i]:
                        self.domains[i].remove(doc)
        return True

    # If a variable has a domain of size 1 - just assign it. Allows for less work to be done from local-search
    def get_initial_assignment(self):
        initial_assignment = [None for _ in range(len(self.variables))]

        for i in range(len(self.variables)):
            if len(self.domains[i]) == 1:
                initial_assignment[i] = self.domains[i][0]

        return initial_assignment

    # Given the start and end date, create a list of date objects representing each day that needs to be filled
    def create_variable_dates(self):
        # Create a curr_date for iterating - starting at the start date
        curr_date = datetime.date(self.start_date.year, self.start_date.month, self.start_date.day)
        time_delta_one = datetime.timedelta(days=1)

        holiday_day_set = set()

        # Better to do this once than have to loop through every time
        for holiday in self.holidays:
            for day in holiday:
                holiday_day_set.add(day)

        variables = []

        # Loop until we are at the end date
        while self.is_valid_date(curr_date):
            # Explicitly consider holidays first
            in_holiday = False
            for holiday in self.holidays:
                if curr_date in holiday:
                    variables.append(holiday)
                    self.holiday_indices.append(len(variables) - 1)
                    in_holiday = True
                while curr_date in holiday:
                    in_holiday = True
                    curr_date += time_delta_one

            if in_holiday:
                continue

            # Weekends: consider next weekend-days as one block (usually 3, could be less if interrupted by holidays)
            # Note that holidays over the weekends encompass the whole weekend explicitly, so we do not do much
            #   to handle any holiday shenanigans here
            is_weekend = False
            weekend = []
            while curr_date.weekday() > 3:
                is_weekend = True
                weekend.append(curr_date)
                curr_date += time_delta_one

            if is_weekend:
                variables.append(tuple(weekend))
                continue

            variables.append(curr_date)
            curr_date += time_delta_one

        return variables

    # Parses the call file to gather all relevant information, such as whether there is a weekday schedule that is
    #   already defined (might be necessary depending on hospital/practice). Otherwise, we can use the given available
    #   weekdays
    def parse_call_file_wrapper(self, call_file_path):
        file_obj = open(call_file_path, "r")
        first_line = file_obj.readline()
        first_line = first_line.strip()
        self.parse_call_file(file_obj, first_line)
        file_obj.close()

    # Recursively evaluates all commands in the file, no matter their order
    # Base case --> curr_line reaches EOF, or there are no valid commands (and we print to stderr before continuing)
    def parse_call_file(self, file_obj, curr_line):
        # Only one of these should be in the file
        if curr_line == "/defined_weekday_assignment":
            curr_line = self.__defined_weekday_assignment_parse(file_obj)
            self.parse_call_file(file_obj, curr_line)
            return
        elif curr_line == "/doctor_available_weekdays":
            curr_line = self.__doctor_available_weekdays_parse(file_obj)
            self.parse_call_file(file_obj, curr_line)
            return

        # Unavailable days for the doctors
        if curr_line == "/doctor_unavailable_days":
            curr_line = self.__doctor_unavailable_days_parse(file_obj)
            self.parse_call_file(file_obj, curr_line)
            return

        # Holiday ranges
        if curr_line == "/holiday_dates":
            curr_line = self.__holiday_dates_parse(file_obj)
            self.parse_call_file(file_obj, curr_line)
            return

        # Allows special treatment of doctors so that they have only so many weekdays or weekends
        if curr_line == "/max_weekends" or curr_line == "/max_weekdays":
            curr_line = self.__max_doctor_days_parse(file_obj, curr_line)
            self.parse_call_file(file_obj, curr_line)
            return

        # Other doctors not mentioned elsewhere that should be added onto the schedule (probably just holidays/weekends)
        if curr_line == "/additional_doctors":
            curr_line = self.__other_doctors_parse(file_obj)
            self.parse_call_file(file_obj, curr_line)
            return

        # Invalid command
        if curr_line:
            print(f"Invalid command or line: {curr_line}", file=sys.stderr)

        return

    # Parses the weekday assignment lines to build the weekday_schedule
    # Returns the (stripped) line that starts a new command, or None if we reach EOF
    def __defined_weekday_assignment_parse(self, file_obj):

        curr_line = file_obj.readline()
        curr_line = curr_line.strip()
        # Go until the file is over, or until we reach a new section
        while curr_line and curr_line[0] != "/":
            # We expect four doctors per line, split by ", " (comma and space)
            doctor_assignments = curr_line.split(", ")
            # Add the doctor to the set if they aren't already there
            for doc in doctor_assignments:
                self.doctors.add(doc)
            # Append the week's schedule
            self.weekday_schedule.append(doctor_assignments)
            # Next line
            curr_line = file_obj.readline()
            curr_line = curr_line.strip()

        # Return whatever line is next (new command or EOF)
        return curr_line

    # Builds the doc_available_weekdays dictionary of available weekdays for each doctor
    # Returns the (stripped) line that starts a new command, or None if we reach EOF
    def __doctor_available_weekdays_parse(self, file_obj):
        curr_line = file_obj.readline()
        curr_line = curr_line.strip()

        # Continue until EOF or until next section
        # Format: doctor; Monday, Wednesday ... (available weekdays separated by ", ")
        while curr_line and curr_line[0] != "/":
            components = curr_line.split("; ")
            # Add the doctor to the doctor set
            self.doctors.add(components[0])

            # Look at the days of the week the doctor is available
            days_of_week = components[1].split(", ")
            for day in days_of_week:
                self.doc_available_weekdays[day].append(components[0])

            curr_line = file_obj.readline()
            curr_line = curr_line.strip()

        return curr_line

    # Builds the doc_unavailable_days dictionary for each doctor
    # Returns the (stripped) line that starts a new command, or None if we reach EOF
    def __doctor_unavailable_days_parse(self, file_obj):
        curr_line = file_obj.readline()
        curr_line = curr_line.strip()

        # Continue until EOF or until next section
        while curr_line and curr_line[0] != "/":
            # Format: doctor; mm/dd/yyyy, mm/dd/yyyy ...
            components = curr_line.split("; ")
            doctor = components[0]
            # Add the doctor to the set if we haven't seen them yet
            self.doctors.add(doctor)

            doc_unavailable_days = components[1].split(", ")
            for unavailable_day in doc_unavailable_days:
                date_parts = unavailable_day.split("/")
                date_obj = datetime.date(int(date_parts[2]), int(date_parts[0]), int(date_parts[1]))
                # Add doctor to unavailable_days dict
                if doctor in self.doc_unavailable_days.keys():
                    self.doc_unavailable_days[doctor].append(date_obj)
                else:
                    self.doc_unavailable_days[doctor] = [date_obj]

            curr_line = file_obj.readline()
            curr_line = curr_line.strip()

        return curr_line

    # Builds the holidays set - a tuple of date(s) for each holiday
    # Returns the (stripped) line that starts a new command, or None if we reach EOF
    def __holiday_dates_parse(self, file_obj):
        curr_line = file_obj.readline()
        curr_line = curr_line.strip()

        while curr_line and curr_line[0] != "/":
            # Format: mm/dd/yyyy, mm/dd/yyyy, mm/dd/yyyy ...
            #   Where the days are only one apart. Allows you to have holidays span more than one day if wanted
            #   For instance - memorial day weekend can be a four-day holiday, so the line would have all four days
            holiday_range = []
            dates = curr_line.split(", ")
            for date in dates:
                date_parts = date.split("/")
                date_obj = datetime.date(int(date_parts[2]), int(date_parts[0]), int(date_parts[1]))
                holiday_range.append(date_obj)
            self.holidays.add(tuple(holiday_range))

            curr_line = file_obj.readline()
            curr_line = curr_line.strip()

        return curr_line

    # Builds the max_weekends or max_weekdays dictionary based on the command in curr_line
    # Returns the (stripped) line that starts a new command, or None if we reach EOF
    def __max_doctor_days_parse(self, file_obj, curr_line):
        # Adjust depending on specific command
        weekends = curr_line == "/max_weekends"
        weekdays = curr_line == "/max_weekdays"

        curr_line = file_obj.readline()
        curr_line = curr_line.strip()
        while curr_line and curr_line[0] != "/":
            components = curr_line.split("; ")
            if weekends:
                self.max_weekends[components[0]] = int(components[1])
            elif weekdays:
                self.max_weekdays[components[0]] = int(components[1])
            curr_line = file_obj.readline()
            curr_line = curr_line.strip()

        return curr_line

    # Adds doctors to the doctors set when who were not mentioned anywhere else, but you still want them on the schedule
    # Returns the (stripped) line that starts a new command, or None if we reach EOF
    def __other_doctors_parse(self, file_obj):
        curr_line = file_obj.readline()
        curr_line = curr_line.strip()
        while curr_line and curr_line[0] != "/":
            self.doctors.add(curr_line)
            curr_line = file_obj.readline()
            curr_line = curr_line.strip()

        return curr_line

    # Use the list of dates as well as all the doctor availability information to create the domains
    def get_domains(self):
        domains = [[] for _ in range(len(self.variables))]

        # Fri Sat Sun considered as one block
        weekday_labels = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday"}

        rand_doc_list = list(self.doctors)
        random.shuffle(rand_doc_list)

        # Give one holiday to each doctor - just hardcode it in the domains
        # TODO: Handle cases of holiday weekends?
        #  Or include it in the holiday dates so that those are on weekends.
        for i in self.holiday_indices:
            # We have fewer doctors than we do distinct holidays. So we need to repeat
            if len(rand_doc_list) == 0:
                rand_doc_list = list(self.doctors)
                random.shuffle(rand_doc_list)

            for doctor in rand_doc_list:
                # We allow doctors to choose holidays as unavailable days
                if self.variables[i] not in self.doc_unavailable_days[doctor]:
                    domains[i] = [doctor]
                    rand_doc_list.remove(doctor)
                    break

        # Used for defined weekday schedules
        curr_weekday_index = 0
        curr_week_index = 0

        # Maps weekdays to a list of doctors
        for date_index in range(len(self.variables)):
            variable = self.variables[date_index]

            # If this is a weekend or holiday block
            if type(variable) == tuple:
                # No more work necessary here if undefined weekly schedule
                if not self.weekday_schedule:
                    continue

                # If it is a holiday, we need to ensure that the rest of the defined schedule is not shifted
                if variable in self.holidays:
                    for day in variable:
                        # This is a weekend day, not relevant
                        if day.weekday() > 3:
                            continue

                        # Weekday holiday, need to continue defined schedule indices
                        curr_weekday_index = (curr_weekday_index + 1) % 4
                        # Wrapped around
                        if curr_weekday_index == 0:
                            curr_week_index = (curr_week_index + 1) % len(self.weekday_schedule)
                continue

            # Define domain to be the defined schedule
            if self.weekday_schedule:
                domains[date_index] = [self.weekday_schedule[curr_week_index][curr_weekday_index]]
                curr_weekday_index = (curr_weekday_index + 1) % 4

                # Wrapped around
                if curr_weekday_index == 0:
                    curr_week_index = (curr_week_index + 1) % len(self.weekday_schedule)
                continue

            # Otherwise get the day of week for an undefined schedule / doctor's have available weekdays
            weekday = weekday_labels[variable.weekday()]

            for avail_doc in self.doc_available_weekdays[weekday]:
                # Check that this specific day is available for that doctor
                if variable not in self.doc_unavailable_days[avail_doc]:
                    domains[date_index].append(avail_doc)

        # Find empty/weekend domains and put all potential doctors in that domain
        for i in range(len(domains)):
            if len(domains[i]) > 0:
                continue

            for doctor in self.doctors:
                # Ensure that there are no unavailable days this weekend block
                if type(self.variables[i]) == tuple:
                    available = True
                    for day in self.variables[i]:
                        if day in self.doc_unavailable_days[doctor]:
                            available = False
                            break
                    if available:
                        domains[i].append(doctor)
                # Otherwise, just check that this date is not unavailable
                elif self.variables[i] not in self.doc_unavailable_days[doctor]:
                    domains[i].append(doctor)

        return domains

    # From the domains and variables, make it that we assign a max of one doctor per day
    def get_constraints(self):
        constraints = dict()

        # No consecutive days or day/weekend pairs for doctors
        length = len(self.variables)
        for var_1 in range(length):
            for var_2 in range(var_1 - 1, min(var_1 + 2, length)):
                if var_1 == var_2:
                    continue

                # Don't mess with consecutive weekdays in a defined schedule
                if self.weekday_schedule:
                    if type(var_1) != tuple and type(var_2) != tuple:
                        continue

                constraints[(var_1, var_2)] = set()

                for doc1 in self.domains[var_1]:
                    for doc2 in self.domains[var_2]:
                        if doc1 != doc2:
                            constraints[(var_1, var_2)].add((doc1, doc2))

        # No consecutive weekends or holiday/weekend
        for var_1 in range(length):
            # This is a weekday, so ignore
            if type(self.variables[var_1]) != tuple:
                continue

            # Within a range of +/- 10 days...
            for var_2 in range(max(var_1 - 10, 0), min(var_1 + 10, length)):
                if var_2 == var_1:
                    continue

                if type(self.variables[var_2]) != tuple:
                    continue

                constraints[(var_1, var_2)] = set()

                for doc1 in self.domains[var_1]:
                    for doc2 in self.domains[var_2]:
                        if doc1 != doc2:
                            constraints[(var_1, var_2)].add((doc1, doc2))

        return constraints

    # Returns True if the date is between the start and end dates, False otherwise
    def is_valid_date(self, date):
        if not self.start_date.year <= date.year <= self.end_date.year:
            return False

        if date.year == self.end_date.year:
            if date.month > self.end_date.month:
                return False
            if date.month == self.end_date.month:
                if date.day > self.end_date.day:
                    return False

        if date.year == self.start_date.year:
            if date.month < self.start_date.month:
                return False
            if date.month == self.start_date.month:
                if date.day < self.start_date.day:
                    return False

        return True

    # Returns three dictionaries given an assignment:
    #  One: A dictionary of the number of weekdays assigned to each doctor
    #  Two: A dictionary of the number of weekends assigned to each doctor
    #  Three: A dictionary of the number of holidays assigned to each doctor
    def get_doc_days_assigned(self, assignment):

        # Initialize dictionaries
        doc_weekdays = dict()
        doc_weekends = dict()
        doc_holidays = dict()
        for doctor in self.doctors:
            doc_weekdays[doctor] = 0
            doc_weekends[doctor] = 0
            doc_holidays[doctor] = 0

        for var in range(len(assignment)):
            # Allows for counting of incomplete assignments
            if assignment[var] is None:
                continue

            # Weekend or holiday assigned
            if type(self.variables[var]) == tuple:
                if self.variables[var] in self.holidays:
                    doc_holidays[assignment[var]] += 1
                else:
                    doc_weekends[assignment[var]] += 1
            else:
                doc_weekdays[assignment[var]] += 1

        return doc_weekdays, doc_weekends, doc_holidays

    def illustrate_solution(self, assignment):
        for i in range(len(self.variables)):
            print("Date: ", self.variables[i])
            print("Doc assigned: ", assignment[i])

    # Writes out the solution week by week to a given file
    def write_out_solution(self, assignment, file_path):
        f = open(file_path, "w")
        line = ""
        max_name_length = 0

        for doc in self.doctors:
            if len(doc) > max_name_length:
                max_name_length = len(doc)

        for var in range(len(assignment)):
            # Weekend or Holiday
            if type(self.variables[var]) == tuple:
                for date in self.variables[var]:
                    # New week
                    if date.weekday() == 0:
                        line += "\n"
                        f.write(line)
                        line = ""

                    num_additional_spaces = max_name_length - len(assignment[var])
                    line += " | " + str(date) + " : " + assignment[var] + (" " * num_additional_spaces) + " | "
                continue

            # New week
            if self.variables[var].weekday() == 0:
                line += "\n"
                f.write(line)
                line = ""
            num_additional_spaces = max_name_length - len(assignment[var])
            line += " | " + str(self.variables[var]) + " : " + assignment[var] + (" " * num_additional_spaces) + " | "

        f.write(line)
        f.close()


if __name__ == "__main__":
    test_1 = CallSchedulingProblem(datetime.date(2024, 1, 15), datetime.date(2025, 1, 15), "testing/definedWeekdays")

    # print(test_1.weekday_schedule)
    # print(test_1.holidays)
    # print(test_1.variables)


    #result = test_1.local_search(10000)

    #print(result)
    # print(test_1.variables)
    #print(len(test_1.variables))
    #print(test_1.domains)
    #print(result)
    #test_1.illustrate_solution(result[0])
    #
    # d1 = datetime.date(2024, 1, 1)
    # d2 = datetime.date(2024, 1, 2)
    # l = [d1, d2]
    #
    # d3 = datetime.date(2024, 1, 1)
    # print(d3 in l)

    # ydc = cal.yeardatescalendar(2023, 1)
    # print(ydc)

    # start_date = datetime.date(2023, 1, 5)
    # curr_date = datetime.date(start_date.year, start_date.month, start_date.day)
    # end_date = datetime.date(2024, 1, 5)
    # time_delta = datetime.timedelta(days=1)
    # dates = []
    # # Until the dates are the same
    # while curr_date.day != end_date.day or curr_date.month != end_date.month or curr_date.year != end_date.year:
    #     print(curr_date)
    #     dates.append(curr_date)
    #     curr_date += time_delta
    # dates.append(end_date)
    # print(dates)