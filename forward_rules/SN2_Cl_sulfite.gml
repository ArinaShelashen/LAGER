rule [
	left [
		node [ id 5 label "O-" ]
		node [ id 3 label "Cl" ]
		edge [ source 5 target 2 label "-" ]
		edge [ source 1 target 3 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "S" ]
		node [ id 4 label "O" ]
		node [ id 7 label "H" ]
		node [ id 6 label "O" ]
		edge [ source 2 target 6 label "-" ]
		edge [ source 2 target 4 label "=" ]
		edge [ source 6 target 7 label "-" ]
	]
	right [
		node [ id 5 label "O" ]
		node [ id 3 label "Cl-" ]
		edge [ source 5 target 2 label "=" ]
		edge [ source 1 target 2 label "-" ]
	]
	constrainAdj [
		id 1
		op "="
		count 0
		edgeLabels [ label ":" label "=" label "#" ]
	]
]