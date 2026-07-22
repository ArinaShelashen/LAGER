rule [
	left [
		edge [ source 6 target 7 label "-" ]
		edge [ source 1 target 2 label "-" ]
	]
	context [
		node [ id 1 label "O" ]
		node [ id 2 label "H" ]
		node [ id 5 label "C" ]
		node [ id 6 label "C" ]
		node [ id 7 label "O" ]
		node [ id 8 label "H" ]
		node [ id 9 label "C" ]
		node [ id 10 label "O" ]
		edge [ source 1 target 5 label "-" ]
		edge [ source 7 target 8 label "-" ]
		edge [ source 6 target 9 label "-" ]
		edge [ source 6 target 10 label "=" ]
	]
	right [
		edge [ source 2 target 7 label "-" ]
		edge [ source 1 target 6 label "-" ]
	]
	constrainAdj [
		id 5
		op "="
		count 2
		edgeLabels [ label ":" ]
	]
	constrainAdj [
		id 9
		op "="
		count 1
		nodeLabels [ label "C" ]
	]
]