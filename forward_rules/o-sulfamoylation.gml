rule [
	ruleID "r_{28}, inverse"
	labelType "term"
	left [
		edge [ source 1 target 2 label "-" ]
		edge [ source 3 target 4 label "-" ]
	]
	context [
		node [ id 0 label "C" ]
		node [ id 1 label "O" ]
		node [ id 2 label "H" ]
		node [ id 3 label "Cl" ]
		node [ id 4 label "S" ]
		node [ id 5 label "O" ]
		node [ id 6 label "N" ]
		node [ id 7 label "O" ]
		edge [ source 0 target 1 label "-" ]
		edge [ source 4 target 5 label "=" ]
		edge [ source 4 target 6 label "-" ]
		edge [ source 4 target 7 label "=" ]
	]
	right [
		edge [ source 1 target 4 label "-" ]
		edge [ source 2 target 3 label "-" ]
	]
]