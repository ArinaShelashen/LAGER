rule [
	labelType "term"
	left [
		edge [ source 3 target 5 label "-" ]
		edge [ source 1 target 6 label "-" ]
		edge [ source 4 target 6 label "-" ]
		edge [ source 1 target 2 label "=" ]
		edge [ source 10 target 11 label "-" ]
		edge [ source 8 target 9 label "-" ]
	]
	context [
		node [ id 1 label "P" ]
		node [ id 2 label "O" ]
		node [ id 3 label "C" ]
		node [ id 4 label "Si" ]
		node [ id 5 label "Br" ]
		node [ id 6 label "O" ]
		node [ id 7 label "C" ]
		node [ id 8 label "O" ]
		node [ id 9 label "Si" ]
		node [ id 10 label "C" ]
		node [ id 11 label "Br" ]
		edge [ source 7 target 1 label "-" ]
		edge [ source 1 target 8 label "-" ]
	]
	right [
		edge [ source 2 target 3 label "-" ]
		edge [ source 4 target 5 label "-" ]
		edge [ source 1 target 6 label "=" ]
		edge [ source 1 target 2 label "-" ]
		edge [ source 8 target 10 label "-" ]
		edge [ source 9 target 11 label "-" ]
	]
	constrainAdj [
		id 3
		op "="
		count 0
		edgeLabels [ label "=" label "#" ]
	]
	constrainAdj [
		id 10
		op "="
		count 0
		edgeLabels [ label "=" label "#" ]
	]
]