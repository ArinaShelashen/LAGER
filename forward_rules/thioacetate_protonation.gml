rule [
	ruleID "r_{23}, inverse"
	labelType "term"
	left [
		node [ id 0 label "S-" ]
		node [ id 5 label "O" ]
		edge [ source 5 target 7 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "C" ]
		node [ id 3 label "O" ]
		node [ id 4 label "C" ]
		node [ id 6 label "O" ]
		node [ id 7 label "H" ]
		edge [ source 0 target 1 label "-" ]
		edge [ source 1 target 2 label "-" ]
		edge [ source 1 target 3 label "=" ]
		edge [ source 6 target 4 label "=" ]
		edge [ source 4 target 5 label "-" ]
	]
	right [
		node [ id 0 label "S" ]
		node [ id 5 label "O-" ]
		edge [ source 7 target 0 label "-" ]
	]
]