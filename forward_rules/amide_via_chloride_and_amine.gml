rule [
	ruleID "r_{4}, inverse"
	labelType "term"
	left [
		edge [ source 0 target 2 label "-" ]
		edge [ source 5 target 7 label "-" ]
	]
	context [
		node [ id 0 label "C" ]
		node [ id 1 label "O" ]
		node [ id 2 label "Cl" ]
		node [ id 3 label "C" ]
		node [ id 4 label "Cl" ]
		node [ id 5 label "N" ]
		node [ id 6 label "C" ]
		node [ id 7 label "H" ]
		edge [ source 0 target 1 label "=" ]
		edge [ source 0 target 3 label "-" ]
		edge [ source 3 target 4 label "-" ]
		edge [ source 5 target 6 label "-" ]
	]
	right [
		edge [ source 0 target 5 label "-" ]
		edge [ source 2 target 7 label "-" ]
	]
]