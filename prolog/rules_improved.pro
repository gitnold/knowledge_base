% rules_improved.pro --- Improved rules for the plant knowledge base
% - Use readable predicate names
% - Provide likely_disease/3: likely_disease(ObservedSymptomsList, Disease, Score)
% - Provide matching_count/3 helper and threshold-based diagnosis helper
% - Keep rules deterministic where possible and document behaviour

:- module(rules_improved, [likely_disease/3, best_diseases/3, disease_symptoms/2]).

% disease_symptoms(Disease, SymptomsList).
% These should match facts in knowledgebase.pro; defining a wrapper helps modularity.
% When using together, consult both knowledgebase.pro and rules_improved.pro in SWI-Prolog.

% Example helper rule (falls back to direct facts if present in knowledgebase):
disease_symptoms(D, Ss) :- disease(D, Ss).

% count how many items from Observed are present in Expected
matching_count(Observed, Expected, Count) :-
    findall(S, (member(S, Observed), member(S, Expected)), Matches),
    length(Matches, Count).

% compute a ratio score = Count / length(Expected)
matching_score(Observed, Expected, Score) :-
    matching_count(Observed, Expected, Count),
    length(Expected, Len),
    ( Len =:= 0 -> Score = 0.0 ; Score is Count / Len ).

% likely_disease(ObservedSymptoms, Disease, Score)
% Score is in [0.0,1.0] representing fraction of disease's symptoms matched by ObservedSymptoms.
likely_disease(Observed, Disease, Score) :-
    disease_symptoms(Disease, Expected),
    matching_score(Observed, Expected, Score),
    Score > 0.0.  % only return diseases with at least one matching symptom

% best_diseases(Observed, Threshold, Results)
% Results is a list of Disease-Score pairs with Score >= Threshold, sorted descending by Score.
best_diseases(Observed, Threshold, Results) :-
    findall(Score-Disease, (likely_disease(Observed, Disease, Score), Score >= Threshold), Pairs),
    keysort(Pairs, Sorted),                % sort ascending by Score
    reverse(Sorted, Rev),                  % now descending
    pairs_to_result_list(Rev, Results).

pairs_to_result_list([], []).
pairs_to_result_list([Score-D|T], [D-Score|R]) :- pairs_to_result_list(T, R).

% Helpful predicates for interactive use:
% diagnose(SymptomsCSV, Threshold) e.g. diagnose("yellowing, wilting", 0.5).
diagnose(SymptomsCSV, Threshold) :-
    split_string(SymptomsCSV, ",", " ", Pieces0),
    maplist(string_lower, Pieces0, Pieces1),
    maplist(string_trim, Pieces1, Pieces),
    best_diseases(Pieces, Threshold, Results),
    writeln(Results).
