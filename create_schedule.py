import sys
import datetime
from CallSchedulingProblem import CallSchedulingProblem

# Author: Ben Williams - benjamin.r.williams.25@dartmouth.edu
# Date: November 29th, 2023

# A very simple script to allow users to create call schedules from the terminal and an input file
# Usage: python create_schedule.py mm/dd/yyyy mm/dd/yyyy input_filepath output_filepath
#                                  ^start date  ^end date

if __name__ == "__main__":
    # Get the start date (mm/dd/yyyy)
    start_date_str = str(sys.argv[1])
    date_parts = start_date_str.split("/")
    start_date = datetime.date(int(date_parts[2]), int(date_parts[0]), int(date_parts[1]))

    # Get the end date (mm/dd/yyyy)
    end_date_str = str(sys.argv[2])
    date_parts = end_date_str.split("/")
    end_date = datetime.date(int(date_parts[2]), int(date_parts[0]), int(date_parts[1]))

    # Get the input file
    input_filepath = str(sys.argv[3])

    # Get the output file-path
    output_filepath = str(sys.argv[4])

    call_prob = CallSchedulingProblem(start_date, end_date, input_filepath)
    schedule = call_prob.solve_for_call_schedule()
    if schedule:
        call_prob.write_out_solution(schedule, output_filepath)
        weekdays, weekends, holidays = call_prob.get_doc_days_assigned(schedule)
        print("Schedule created. Below are the number of weekdays, weekends, and holidays assigned to each doctor:")
        print("Weekday totals:", weekdays)
        print("Weekend totals:", weekends)
        print("Holiday totals:", holidays)

