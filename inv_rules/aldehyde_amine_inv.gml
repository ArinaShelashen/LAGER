rule [
	left [
		edge [ source 2 target 6 label "-" ]
		edge [ source 3 target 7 label "-" ]
		edge [ source 4 target 7 label "-" ]
		edge [ source 2 target 9 label "-" ]
		edge [ source 6 target 10 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "N" ]
		node [ id 3 label "H" ]
		node [ id 4 label "H" ]
		node [ id 6 label "C" ]
		node [ id 7 label "O" ]
		node [ id 8 label "H" ]
		node [ id 9 label "H" ]
		node [ id 10 label "H" ]
		edge [ source 1 target 2 label "-" ]
		edge [ source 6 target 8 label "-" ]
	]
	right [
		edge [ source 6 target 7 label "=" ]
		edge [ source 2 target 3 label "-" ]
		edge [ source 2 target 4 label "-" ]
		edge [ source 9 target 10 label "-" ]
	]
	constrainAdj [
		id 6
		op "="
		count 0
		nodeLabels [ label "O" ]
	]
]