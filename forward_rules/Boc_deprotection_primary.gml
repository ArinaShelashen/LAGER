rule [
	ruleID "r_{42}, inverse"
	left [
		edge [ source 1 target 3 label "-" ]
		edge [ source 2 target 3 label "-" ]
		edge [ source 2 target 5 label "-" ]
		edge [ source 5 target 6 label "-" ]
		edge [ source 5 target 7 label "-" ]
	]
	context [
		node [ id 0 label "C" ]
		node [ id 1 label "N" ]
		node [ id 2 label "O" ]
		node [ id 3 label "C" ]
		node [ id 4 label "O" ]
		node [ id 5 label "C" ]
		node [ id 6 label "C" ]
		node [ id 7 label "H" ]
		node [ id 8 label "H" ]
		edge [ source 0 target 1 label "-" ]
		edge [ source 3 target 4 label "=" ]
		edge [ source 8 target 1 label "-" ]
	]
	right [
		edge [ source 1 target 7 label "-" ]
		edge [ source 2 target 3 label "=" ]
		edge [ source 5 target 6 label "=" ]
	]
	constrainAdj [
		id 0
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
]