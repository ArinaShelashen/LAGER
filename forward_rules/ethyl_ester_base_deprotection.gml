rule [
	left [
		node [ id 5 label "O-" ]
		node [ id 2 label "O" ]
		edge [ source 2 target 1 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 3 label "C" ]
		node [ id 6 label "H" ]
		node [ id 7 label "C" ]
		node [ id 8 label "O" ]
		edge [ source 1 target 3 label "-" ]
		edge [ source 5 target 6 label "-" ]
		edge [ source 2 target 7 label "-" ]
		edge [ source 7 target 8 label "=" ]
	]
	right [
		node [ id 5 label "O" ]
		node [ id 2 label "O-" ]
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
		nodeLabels [ label "C" label "O" label "O-" ]
	]
]