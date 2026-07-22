rule [
	ruleID "r_{7}, inverse"
	left [
		edge [ source 1 target 2 label "#" ]
		edge [ source 3 target 5 label "-" ]
		edge [ source 3 target 6 label "-" ]
	]
	context [
		node [ id 0 label "S" ]
		node [ id 1 label "C" ]
		node [ id 2 label "N" ]
		node [ id 3 label "O" ]
		node [ id 4 label "C" ]
		node [ id 5 label "H" ]
		node [ id 6 label "H" ]
		edge [ source 0 target 1 label "-" ]
		edge [ source 0 target 4 label "-" ]
	]
	right [
		edge [ source 1 target 2 label "-" ]
		edge [ source 1 target 3 label "=" ]
		edge [ source 2 target 5 label "-" ]
		edge [ source 2 target 6 label "-" ]
	]
]