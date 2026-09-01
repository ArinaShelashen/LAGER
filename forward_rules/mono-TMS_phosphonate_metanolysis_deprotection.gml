rule [
	labelType "term"
	left [
		edge [ source 5 target 6 label "-" ]
		edge [ source 2 target 4 label "-" ]
	]
	context [
		node [ id 2 label "O" ]
		node [ id 4 label "Si" ]
		node [ id 5 label "O" ]
		node [ id 6 label "H" ]
		node [ id 11 label "P" ]
		node [ id 21 label "C" ]
		node [ id 22 label "C" ]
		node [ id 23 label "C" ]
		edge [ source 11 target 2 label "-" ]
		edge [ source 21 target 5 label "-" ]
		edge [ source 22 target 11 label "-" ]
		edge [ source 23 target 11 label "-" ]
	]
	right [
		edge [ source 4 target 5 label "-" ]
		edge [ source 2 target 6 label "-" ]
	]
	constrainAdj [
		id 11
		op "="
		count 1
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 21
		op "="
		count 3
		nodeLabels [ label "H" ]
	]
]