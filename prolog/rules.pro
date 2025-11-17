% This rule is true if Element is a member of the List.
member(Element, [Element | _]).
member(Element, [_ | Rest]) :- member(Element, Rest).

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
