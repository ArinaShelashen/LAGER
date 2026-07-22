rule [
	left [
		edge [ source 3 target 1 label "-" ]
		edge [ source 2 target 4 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "O" ]
		node [ id 3 label "N" ]
		node [ id 4 label "H" ]
		node [ id 5 label "O" ]
		node [ id 6 label "C" ]
		node [ id 7 label "H" ]
		edge [ source 2 target 6 label "-" ]
		edge [ source 7 target 3 label "-" ]
		edge [ source 5 target 1 label "=" ]
	]
	right [
		edge [ source 3 target 4 label "-" ]
		edge [ source 1 target 2 label "-" ]
	]
	constrainAdj [
		id 3
		op "="
		count 1
		nodeLabels [ label "C" ]
	]
	constrainAdj [
		id 6
		op "<="
		count 1
		nodeLabels [ label "C" ]
	]
]