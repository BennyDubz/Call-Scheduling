from collections import deque
import random
import copy
from csp_helper_functions import *

# Author: Ben Williams '25
# Date: October 8th, 2023


class ConstraintSatisfactionProblem:
    def __init__(self, variables, domains, constraints):
        self.variables = variables
        self.domains = domains
        self.constraints = constraints
        self.total_search_calls = 0

    # Recursive solver that tries every possibility until we find one that works
    # Returns a list of assignments if there is a valid solution, and None if there is no solution
    def brute_force_solver(self, variable_index=0, curr_assignment=None):
        if not curr_assignment:
            curr_assignment = [None for i in range(len(self.variables))]

        self.total_search_calls += 1

        # Base case
        if variable_index == len(self.variables):
            if self.is_valid_assignment(curr_assignment):
                return curr_assignment
            return None

        # Try all possible values
        for possible_value in self.domains[variable_index]:
            curr_assignment[variable_index] = possible_value
            result = self.brute_force_solver(variable_index + 1, curr_assignment)

            # If it is not none
            if result:
                return result

        # We failed to find a valid assignment (at this depth)
        return None

    # Given an assignment, check if it is valid or not
    # Returns True if valid, False otherwise
    def is_valid_assignment(self, assignment):
        for (variable, possible_conflict) in self.constraints.keys():
            # Check if the assignment is in the set of allowed constraints
            assigned_pair = assignment[variable], assignment[possible_conflict]
            if assigned_pair not in self.constraints[(variable, possible_conflict)]:
                return False

        return True

    # Recursive solver that uses backtracking to find a valid assignment
    # It can also use heuristics alongside inference to speed up the search
    def backtracking_solver(self, assignment=None, domains=None, inference=None, select_variable=None, order_domain=None):
        self.total_search_calls += 1

        # Instantiate the assignment and domains if they don't exist
        if not assignment:
            assignment = [None for i in range(len(self.variables))]
        if not domains:
            # Copy the self.domains into domains so that the self.domains is unaltered
            # We need the copy.deepcopy() because we are copying a list of objects (lists), which takes more effort
            domains = copy.deepcopy(self.domains)

        # Select the unassigned variable via the heuristic if it is available
        if select_variable:
            variable = select_variable(assignment, domains)
        # Otherwise, just select the first unassigned variable
        else:
            variable = first_unassigned_variable(assignment)

        # Base case - We could not find an unassigned variable
        if variable is None:
            return assignment

        # Use an ordered domain heuristic if it is available
        if order_domain:
            variable_domain = order_domain(variable, assignment, domains)
        # Otherwise, just get the domain for the variable (stored in our curr_assignment)
        else:
            variable_domain = domains[variable]

        # Loop through all possible values we could assign this variable
        for value in variable_domain:
            # Ignore inconsistent values
            if not self.is_consistent_value(variable, value, assignment):
                continue

            # Partial assignment of this value
            assignment[variable] = value

            if inference:
                inference_success, removed_values = inference(variable, value, assignment, domains)
            # We do not perform any inference, and therefore always continue
            else:
                inference_success, removed_values = True, []

            # Either the inference succeeded, or we were not performing it
            if inference_success:
                # Prune the domains (will not do anything if there is no inference)
                remove_from_domains(removed_values, domains)

                result = self.backtracking_solver(assignment, domains, inference, select_variable, order_domain)

                # If the search was a success
                if result:
                    return result

            # Reset the assignment to None, value does not work for this assignment
            assignment[variable] = None
            # Restore the domains to their original state
            if removed_values:
                add_to_domains(removed_values, domains)

        return None

    # Checks if this value that we are assigning this variable is consistent with our current assignment
    # Returns True if consistent, False otherwise
    def is_consistent_value(self, variable, value, assignment):
        for assigned_var in range(len(assignment)):
            # Ignore currently unassigned values
            if assignment[assigned_var] is None:
                continue

            # Check for an illegal assignment
            if (assigned_var, variable) in self.constraints.keys():
                if (assignment[assigned_var], value) not in self.constraints[(assigned_var, variable)]:
                    return False

        # None of the assignments are illegal
        return True

    # Returns the stored number of search calls and resets it to zero
    def get_and_reset_search_calls(self):
        search_calls = self.total_search_calls
        self.total_search_calls = 0
        return search_calls

    # MAC3 Inference algorithm that only makes changes around the given variables neighbors
    def MAC3(self, variable, value, assignment, domains):
        queue = deque()
        # Add all (neighbor, variable) pairs to the queue for unassigned neighbors
        variable_neighbors = self.get_neighbors(variable)
        for neighbor in variable_neighbors:
            if assignment[neighbor] is not None:
                queue.append((neighbor, variable))

        total_remove_list = [[] for i in range(len(self.variables))]
        while len(queue) > 0:
            arc = queue.popleft()
            # Find the values to remove from the neighbor's domain
            total_remove_list[arc[0]] = self.MAC3_revise_domains(arc[0], arc[1], domains, value)
            # If we are removing every single value from the neighbor's domain
            if len(total_remove_list[arc[0]]) == len(domains[arc[0]]):
                # If there are no possible values for the variable arc[0] that satisfy the arc
                return False, None

        # There are still valid assignments for all the neighbors
        return True, total_remove_list

    # Used in inference to modify the domains of var_1 given var_2, where var_2 already has an assignment
    # Returns a list of values to be removed
    def MAC3_revise_domains(self, var_1, var_2, domains, value):
        remove_list = []
        # We may delete values in domains[var_1]
        for i in range(len(domains[var_1]) - 1, -1, -1):
            # Try to find a valid assignment for var_1, var_2, given var_2 already has an assigned value
            if (domains[var_1][i], value) not in self.constraints[(var_1, var_2)]:
                remove_list.append(domains[var_1][i])
        return remove_list

    # Returns a list of neighbors of the given variable
    def get_neighbors(self, variable):
        variable_neighbors = []
        for other_var in self.variables:
            if (other_var, variable) in self.constraints.keys():
                variable_neighbors.append(other_var)
        return variable_neighbors

    # Sorts the possible values for the variable into a list from least-constraining to most-constraining
    def least_constraining_value(self, variable, assignment, domains):
        num_available = [0 for i in range(len(domains[variable]))]
        for other_var in self.variables:
            index = 0

            # If we only want to consider constraints with non-assigned variables
            if assignment[other_var] is not None:
                continue

            # If these variables are not neighbors
            if (variable, other_var) not in self.constraints.keys():
                continue

            # Loop through all value combinations
            for value in domains[variable]:
                for other_value in domains[other_var]:
                    # If this pair is allowed
                    if (value, other_value) in self.constraints[(variable, other_var)]:
                        num_available[index] += 1
                index += 1

        # Get the sorted indices for the ordered domain
        indexes = [i for i in range(len(domains[variable]))]
        indexes.sort(key=num_available.__getitem__)

        # Get the actual values in the right spots
        ordered_domain = list(map(domains[variable].__getitem__, indexes))

        # We want it to be from high --> low
        ordered_domain.reverse()
        return ordered_domain

    # Calls a local search using min-conflicts and a random-walk
    # Returns a valid assignment (if found) and the number of iterations it took to find it
    def local_search(self, max_iters, assignment=None, use_visited=False, print_iters=False):
        # Either generate a completely random assignment from each variable's domain
        empty_indices = set()
        if not assignment:
            assignment = [random.choice(self.domains[i]) for i in range(len(self.variables))]
            editing_given_assignment = False
        # Or fill in just the empty values of the assignment, and only edit those
        else:
            editing_given_assignment = True
            for i in range(len(assignment)):
                if assignment[i] is None:
                    assignment[i] = random.choice(self.domains[i])
                    empty_indices.add(i)

        conflicted_variables = self.get_conflicted_variables(assignment)

        # If we are editing a given assignment, do not adjust other variables
        if editing_given_assignment:
            for var in conflicted_variables:
                if var not in empty_indices:
                    conflicted_variables.remove(var)

        # If by some miracle our random assignment worked
        if not conflicted_variables:
            return assignment, 0

        # Do not re-visit recently revisited states (tabu search)
        recently_visited = [[] for i in range(2)]

        # The total number of iterations
        curr_iters = 0

        # While there is a conflicting variable
        while len(conflicted_variables) > 0:
            if curr_iters > max_iters:
                if print_iters:
                    print("Maximum number of iterations reached")
                return None, curr_iters

            curr_iters += 1
            # Randomly select the variable
            variable = random.choice(conflicted_variables)

            # Assign the value that violates the fewest constraints
            # We break ties randomly
            least_constraining_values = self.violates_least_constraints(variable, assignment)
            assignment[variable] = random.choice(least_constraining_values)

            # Do not revisit recently seen states, and switch it up to avoid plateaus or local minima
            if use_visited:
                if assignment in recently_visited:
                    switch_up = random.choice(self.variables)
                    assignment[switch_up] = random.choice(self.domains[switch_up])

                recently_visited.pop()
                recently_visited.insert(0, assignment)

            conflicted_variables = self.get_conflicted_variables(assignment)
            if editing_given_assignment:
                for var in conflicted_variables:
                    if var not in empty_indices:
                        conflicted_variables.remove(var)

        if print_iters:
            print("Total loops", curr_iters)

        return assignment, curr_iters

    # Returns a list of values that all conflict the least amount possible
    def violates_least_constraints(self, variable, assignment):
        num_conflicts = [0 for i in range(len(self.domains[variable]))]
        index = 0
        # Loop through all possible values
        for value in self.domains[variable]:
            # Check other values in the (complete) assignment
            for other_var in range(len(assignment)):
                if other_var == variable:
                    continue

                if (variable, other_var) not in self.constraints.keys():
                    continue

                # If this value violates a constraint between these two variables
                if (value, assignment[other_var]) not in self.constraints[(variable, other_var)]:
                    num_conflicts[index] += 1

            index += 1

        min_conflicts = min(num_conflicts)

        # How long can I make it?
        best_values = [self.domains[variable][i] for i in range(len(self.domains[variable]))
                       if num_conflicts[i] == min_conflicts]

        return best_values

    # Returns a list of all the conflicted variables in the assignment
    def get_conflicted_variables(self, assignment):
        conflicted_variables = set()

        # Check all pairs
        for var_1 in range(len(assignment)):
            for var_2 in range(len(assignment)):
                # To speed this up a bit
                if var_1 in conflicted_variables or var_2 in conflicted_variables:
                    continue

                # If these variables are not neighbors
                if (var_1, var_2) not in self.constraints.keys():
                    continue

                # If the variables conflict
                if (assignment[var_1], assignment[var_2]) not in self.constraints[(var_1, var_2)]:
                    conflicted_variables.add(var_1)
                    conflicted_variables.add(var_2)

        # We want it in list format, but the order is irrelevant
        return list(conflicted_variables)

