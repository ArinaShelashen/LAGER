rule [
	ruleID "r_{23}, inverse"
	labelType "term"
	left [
		node [ id 0 label "S-" ]
		node [ id 5 label "Cl" ]
		edge [ source 4 target 5 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "C" ]
		node [ id 3 label "O" ]
		node [ id 4 label "C" ]
		edge [ source 0 target 1 label "-" ]
		edge [ source 1 target 2 label "-" ]
		edge [ source 1 target 3 label "=" ]
	]
	right [
		node [ id 0 label "S" ]
		node [ id 5 label "Cl-" ]
		edge [ source 0 target 4 label "-" ]
	]
	constrainAdj [
		id 4
		op "="
		count 0
		edgeLabels [ label "=" label ":" label "#" ]
	]
]