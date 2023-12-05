import sys
import datetime
from CallSchedulingProblem import CallSchedulingProblem

# Author: Ben Williams - benjamin.r.williams.25@dartmouth.edu
# Date: November 29th, 2023

# A very simple script to allow users to create call schedules from the terminal and an input file
# Usage: python create_schedule.py mm/dd/yyyy mm/dd/yyyy input_filepath output_filepath
#                                  ^start date  ^end date
# The output_filepath is optional, and will just output into the current directory if no path is provided

if __name__ == "__main__":
    if len(sys.argv) not in [4, 5]:
        print("Incorrect amount of parameters given. Please give a start date, end date, input filepath, "
              "and output filepath separated by spaces.",
              "\nIt should look like:: python create_schedule.py mm/dd/yyyy mm/dd/yyyy input_filepath output_filepath",
              file=sys.stderr)
        exit(1)

    # Get the start date (mm/dd/yyyy)
    start_date_str = str(sys.argv[1])
    date_parts = start_date_str.split("/")
    try:
        start_date = datetime.date(int(date_parts[2]), int(date_parts[0]), int(date_parts[1]))
    except ValueError:
        print(f"Invalid start date format {start_date_str}. Please give it in mm/dd/yyyy format.", file=sys.stderr)
        exit(2)

    # Get the end date (mm/dd/yyyy)
    end_date_str = str(sys.argv[2])
    date_parts = end_date_str.split("/")
    try:
        end_date = datetime.date(int(date_parts[2]), int(date_parts[0]), int(date_parts[1]))
    except ValueError:
        print(f"Invalid start date format {end_date_str}. Please give it in mm/dd/yyyy format.", file=sys.stderr)
        exit(3)

    # Get the input file
    input_filepath = str(sys.argv[3])
    try:
        f = open(input_filepath, "r")
        f.close()
    except FileNotFoundError:
        print(f"Invalid input filepath {input_filepath}, cannot find or open file", file=sys.stderr)
        exit(4)

    # Get the output file-path
    if len(sys.argv) == 5:
        output_filepath = str(sys.argv[4])
    else:
        output_filepath = "./"

    try:
        if output_filepath[-1] == "/":
            f = open(output_filepath + "output_schedule.txt", "w")
        else:
            f = open(output_filepath)
        f.close()
    except FileNotFoundError:
        print(f"Unable to create file at {output_filepath}. The directory may not exist, or you may not have permission"
              , file=sys.stderr)
        exit(5)

    call_prob = CallSchedulingProblem(start_date, end_date, input_filepath)
    schedule = call_prob.solve_for_call_schedule()

    if schedule:
        call_prob.write_out_solution(schedule, output_filepath)
        weekdays, weekends, holidays = call_prob.get_doc_days_assigned(schedule)
        print("Schedule created. Below are the number of weekdays, weekends, and holidays assigned to each doctor:")
        print("Weekday totals:", weekdays)
        print("Weekend totals:", weekends)
        print("Holiday totals:", holidays)

