rule [
	ruleID "r_{19}, inverse"
	labelType "term"
	left [
		edge [ source 0 target 1 label "-" ]
		edge [ source 5 target 6 label "-" ]
	]
	context [
		node [ id 0 label "S" ]
		node [ id 1 label "C" ]
		node [ id 2 label "C" ]
		node [ id 3 label "O" ]
		node [ id 4 label "C" ]
		node [ id 5 label "O-" ]
		node [ id 6 label "H" ]
		edge [ source 0 target 4 label "-" ]
		edge [ source 1 target 2 label "-" ]
		edge [ source 1 target 3 label "=" ]
	]
	right [
		edge [ source 0 target 6 label "-" ]
		edge [ source 1 target 5 label "-" ]
	]
]