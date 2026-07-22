rule [
	left [
		edge [ source 2 target 1 label "-" ]
		edge [ source 4 target 5 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "O" ]
		node [ id 3 label "C" ]
		node [ id 4 label "H" ]
		node [ id 5 label "O" ]
		node [ id 6 label "H" ]
		node [ id 7 label "P" ]
		edge [ source 1 target 3 label "-" ]
		edge [ source 5 target 6 label "-" ]
		edge [ source 2 target 7 label "-" ]
	]
	right [
		edge [ source 2 target 4 label "-" ]
		edge [ source 1 target 5 label "-" ]
	]
	constrainAdj [
		id 3
		op "="
		count 1
		nodeLabels [ label "C" ]
	]
	constrainAdj [
		id 1
		op "="
		count 2
		nodeLabels [ label "C" label "O" ]
	]
]