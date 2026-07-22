rule [
	left [
		node [ id 1 label "S" ]
		node [ id 6 label "Br-" ]
		edge [ source 5 target 1 label "-" ]
	]
	context [
		node [ id 2 label "C" ]
		node [ id 3 label "C" ]
		node [ id 4 label "O" ]
		node [ id 5 label "C" ]
		edge [ source 2 target 4 label "=" ]
		edge [ source 2 target 3 label "-" ]
		edge [ source 1 target 2 label "-" ]
	]
	right [
		node [ id 1 label "S-" ]
		node [ id 6 label "Br" ]
		edge [ source 5 target 6 label "-" ]
	]
	constrainAdj [
		id 5
		op "="
		count 0
		edgeLabels [ label "=" label ":" label "#" ]
	]
]