rule [
	labelType "term"
	left [
		edge [ source 4 target 5 label "-" ]
		edge [ source 2 target 6 label "-" ]
		edge [ source 19 target 12 label "-" ]
		edge [ source 18 target 13 label "-" ]
	]
	context [
		node [ id 2 label "O" ]
		node [ id 4 label "Si" ]
		node [ id 5 label "O" ]
		node [ id 6 label "H" ]
		node [ id 11 label "P" ]
		node [ id 12 label "O" ]
		node [ id 13 label "Si" ]
		node [ id 18 label "O" ]
		node [ id 19 label "H" ]
		node [ id 20 label "C" ]
		node [ id 21 label "C" ]
		edge [ source 11 target 2 label "-" ]
		edge [ source 11 target 12 label "-" ]
		edge [ source 21 target 5 label "-" ]
		edge [ source 20 target 18 label "-" ]
	]
	right [
		edge [ source 5 target 6 label "-" ]
		edge [ source 2 target 4 label "-" ]
		edge [ source 12 target 13 label "-" ]
		edge [ source 19 target 18 label "-" ]
	]
	constrainAdj [
		id 11
		op "="
		count 1
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 20
		op "="
		count 3
		nodeLabels [ label "H" ]
	]
	constrainAdj [
		id 21
		op "="
		count 3
		nodeLabels [ label "H" ]
	]
]