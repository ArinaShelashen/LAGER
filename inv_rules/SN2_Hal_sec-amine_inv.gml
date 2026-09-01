rule [
	labelType "term"
	left [
		edge [ source 1 target 3 label "-" ]
		edge [ source 4 target 2 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "_X" ]
		node [ id 3 label "N" ]
		node [ id 4 label "H" ]
		node [ id 5 label "C" ]
		node [ id 6 label "C" ]
		edge [ source 3 target 5 label "-" ]
		edge [ source 3 target 6 label "-" ]
	]
	right [
		edge [ source 1 target 2 label "-" ]
		edge [ source 3 target 4 label "-" ]
	]
	constrainAdj [
		id 1
		op "="
		count 0
		edgeLabels [ label ":" label "=" label "#" ]
	]
	constrainAdj [
		id 5
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 6
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainLabelAny [ label "_X" labels [ label "Br" label "I" ] ]
]