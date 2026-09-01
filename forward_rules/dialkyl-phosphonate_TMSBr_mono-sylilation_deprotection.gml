rule [
	labelType "term"
	left [
		edge [ source 2 target 3 label "-" ]
		edge [ source 4 target 5 label "-" ]
		edge [ source 1 target 6 label "=" ]
		edge [ source 1 target 2 label "-" ]
	]
	context [
		node [ id 1 label "P" ]
		node [ id 2 label "O" ]
		node [ id 3 label "C" ]
		node [ id 4 label "Si" ]
		node [ id 5 label "Br" ]
		node [ id 6 label "O" ]
		node [ id 7 label "C" ]
		node [ id 8 label "C" ]
		edge [ source 7 target 1 label "-" ]
		edge [ source 8 target 1 label "-" ]
	]
	right [
		edge [ source 3 target 5 label "-" ]
		edge [ source 1 target 6 label "-" ]
		edge [ source 4 target 6 label "-" ]
		edge [ source 1 target 2 label "=" ]
	]
	constrainAdj [
		id 3
		op "="
		count 0
		edgeLabels [ label "=" label "#" ]
	]
]