% This rule is true if Element is a member of the List.
member(Element, [Element | _]).
member(Element, [_ | Rest]) :- member(Element, Rest).

% member(Element, List) is true if Element is in the List.
member(X, [X | _]).
member(X, [_ | Tail]) :- member(X, Tail).

is_disease(Disease) :-
    disease(Disease).

is_pest(Pest) :-
    pest(Pest).

% 'Problem' is found in 'Region' IF
%   1. The 'found' fact for 'Problem' has a 'RegionList', AND
%   2. 'Region' is a member of that 'RegionList'.

problem_in_region(Problem, Region) :-
    found(Problem, RegionList),
    member(Region, RegionList).

% 'Treatment' is a treatment for 'Problem' IF
%   1. The 'treatments' fact for 'Problem' has a 'TreatmentList', AND
%   2. 'Treatment' is a member of that 'TreatmentList'.

find_treatment(Problem, Treatment) :-
    treatments(Problem, TreatmentList),
    member(Treatment, TreatmentList).

% 'Problem' might be the cause IF you see 'Symptom'
problem_from_symptom(Symptom, Problem) :-
    has_symptom(Problem, Symptom).

% 'Problem' is managed by 'Method'
find_problem_by_control(Method, Problem) :-
    uses_control(Problem, Method).

% find_treatment/2 is the simple rule from my last answer
find_treatment(Problem, Treatment) :-
    treatments(Problem, TreatmentList),
    member(Treatment, TreatmentList).

% common_treatment is true if Treatment works for two DIFFERENT problems
common_treatment(Treatment, Problem1, Problem2) :-
    find_treatment(Problem1, Treatment),
    find_treatment(Problem2, Treatment),
    Problem1 \= Problem2.  % The \= operator means "not equal".

% diagnose/2 is true if the Problem exhibits ALL symptoms in the SymptomList.
diagnose(Problem, SymptomList) :-
    forall(member(Symptom, SymptomList), has_symptom(Problem, Symptom)).

% uses_multiple_controls/1 is true if a Problem has at least two
% different control methods listed.
uses_multiple_controls(Problem) :-
    uses_control(Problem, Method1),
    uses_control(Problem, Method2),
    Method1 \= Method2.
