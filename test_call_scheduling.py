from CallSchedulingProblem import CallSchedulingProblem
import datetime

# Author: Ben Williams - benjamin.r.williams.25@dartmouth.edu
# Date: November 6th, 2023

curr_file = "examples/definedWeekdays"
# curr_file = "examples/definedWeekdays"
start_date = datetime.date(2024, 1, 15)
end_date = datetime.date(2025, 1, 15)

call_s = CallSchedulingProblem(start_date, end_date, curr_file)
# print(len(call_s.variables))
# print(len(call_s.domains))
# print(call_s.domains)

result = call_s.solve_for_call_schedule(print_info=True)

weekdays, weekends, holidays = call_s.get_doc_days_assigned(result)
print("Result: ", result)
print("Weekday totals:",  weekdays)
print("Weekend totals:", weekends)
print("Holiday totals:", holidays)

call_s.write_out_solution(result, "example_results/defined_weekdays_results")

# result_backtrack = call_s.backtracking_solver()
# doc_count = dict()
# for doc in call_s.doctors:
#     doc_count[doc] = 0
#
# for result in result_backtrack:
#     doc_count[result] += 1

# print("Backtracking doc count:", doc_count)
# for doc in call_s.doctors:
#     doc_count[doc] = 0
# for i in range(100):
#     result_local_search = call_s.local_search(10000)
#     if not result_local_search:
#         print("Failed")
#         continue
#
#     for result in result_local_search[0]:
#         doc_count[result] += 1
#
# print("Local search doc count:", doc_count)
#
# avg_doc_count = [doc_count[i] / 100 for i in doc_count.keys()]
# print("Avg doc count:", avg_doc_count)



