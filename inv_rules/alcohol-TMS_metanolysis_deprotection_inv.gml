rule [
	labelType "term"
	left [
		edge [ source 4 target 5 label "-" ]
		edge [ source 2 target 6 label "-" ]
	]
	context [
		node [ id 2 label "O" ]
		node [ id 4 label "Si" ]
		node [ id 5 label "O" ]
		node [ id 6 label "H" ]
		node [ id 7 label "C" ]
		node [ id 8 label "C" ]
		node [ id 9 label "C" ]
		node [ id 10 label "C" ]
		node [ id 11 label "C" ]
		edge [ source 5 target 7 label "-" ]
		edge [ source 10 target 4 label "-" ]
		edge [ source 9 target 4 label "-" ]
		edge [ source 8 target 4 label "-" ]
		edge [ source 11 target 2 label "-" ]
	]
	right [
		edge [ source 5 target 6 label "-" ]
		edge [ source 2 target 4 label "-" ]
	]
	constrainAdj [
		id 7
		op "="
		count 3
		nodeLabels [ label "H" ]
	]
	constrainAdj [
		id 8
		op "="
		count 3
		nodeLabels [ label "H" ]
	]
	constrainAdj [
		id 9
		op "="
		count 3
		nodeLabels [ label "H" ]
	]
	constrainAdj [
		id 10
		op "="
		count 3
		nodeLabels [ label "H" ]
	]
	constrainAdj [
		id 11
		op "="
		count 0
		edgeLabels [ label "=" label "#" ]
	]
	constrainAdj [
		id 11
		op "="
		count 0
		nodeLabels [ label "N" ]
	]
	constrainAdj [
		id 11
		op "="
		count 1
		nodeLabels [ label "O" ]
	]
]