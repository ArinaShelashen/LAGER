rule [
	ruleID "r_{26}, inverse"
	left [
		edge [ source 0 target 1 label "-" ]
		edge [ source 2 target 3 label "-" ]
	]
	context [
		node [ id 0 label "N" ]
		node [ id 1 label "H" ]
		node [ id 2 label "C" ]
		node [ id 3 label "Cl" ]
		node [ id 4 label "O" ]
		edge [ source 2 target 4 label "=" ]
	]
	right [
		edge [ source 0 target 2 label "-" ]
		edge [ source 1 target 3 label "-" ]
	]
]