# Doctor Call Scheduler
### Author: Ben Williams - benjamin.r.williams.25@dartmouth.edu

## The Problem and the Purpose

The orthopaedic practice in my hometown has to spend many hours negotiating and creating a fair call schedule for an entire year. The "call schedule" represents the doctor that is on-call during that day, and can be called in at anytime (even 1 AM for instance) during that day/night to help someone with an emergency at the hospital.

Naturally, the days that a doctor is on call affect their quality of life and need to be factored into how they plan their year. If they have an obligation to be on call one weekend, they cannot go to their child's sporting event or plan a trip - and are overall more limited in what they can do. Or, since doctors are often assigned specific holidays, they cannot travel on those holidays. Therefore, it is important for them to know the call schedule ahead of time and for it to be fair as it is a burden that the doctors need to share amongst themselves.

But making a fair call schedule that can handle each doctor's preferences or needs, has quality of life assurances, and can handle specific seniority agreements (some doctors get less call than others), can take a __long time__. These are made a full year in advance, and in speaking to those who have made these schedules before, they often use pencil and paper, __lots of eraser__, and roughly 10 hours of time.

This program frames this problem as a constraint satisfaction problem, and uses repeated local search (see `ConstraintSatisfactionProblem.py`) to create a schedule that fulfills all the local (quality of life) and global (fairness) constraints. While the local search that does the bulk of the work is simple, framing the problem and its input into the variables/domains/constraints is what makes the bulk of `CallSchedulingProblem.py`.

## Usage

