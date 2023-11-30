from math import inf
# Author: Ben Williams
# Date: October 12th, 2023


# Returns the index of a currently unassigned variable, or None if they are all filled
def first_unassigned_variable(assignment):
    for i in range(len(assignment)):
        if assignment[i] is None:
            return i
    return None


# Returns the index of the currently unassigned variable with the fewest remaining possible values
def minimum_remaining_values(assignment, domains):
    # Infinite domain size to start
    min_available_size = inf
    min_available_index = None
    for i in range(len(assignment)):
        if assignment[i] is None:
            # If the size of this domain is the smallest seen so far
            if len(domains[i]) < min_available_size:
                min_available_index = i
                min_available_size = len(domains[i])

    return min_available_index


# Given a list of lists of values to remove and the domains, remove the values from the domain
def remove_from_domains(remove_lists, domains):
    for i in range(len(remove_lists)):
        for removal in remove_lists[i]:
            domains[i].remove(removal)


# Given a list of lists of values to add and the domains, add the values from the domain
# Used to return the domains to their previous state after removing values
def add_to_domains(add_lists, domains):
    for i in range(len(add_lists)):
        for addition in add_lists[i]:
            domains[i].append(addition)
