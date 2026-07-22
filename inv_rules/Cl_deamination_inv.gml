rule [
	left [
		edge [ source 1 target 9 label "-" ]
		edge [ source 2 target 5 label "#" ]
		edge [ source 3 target 6 label "-" ]
		edge [ source 4 target 6 label "-" ]
		edge [ source 10 target 7 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "N" ]
		node [ id 3 label "H" ]
		node [ id 4 label "H" ]
		node [ id 5 label "N" ]
		node [ id 6 label "O" ]
		node [ id 7 label "O" ]
		node [ id 8 label "H" ]
		node [ id 9 label "Cl" ]
		node [ id 10 label "H" ]
		edge [ source 7 target 8 label "-" ]
	]
	right [
		edge [ source 9 target 10 label "-" ]
		edge [ source 1 target 2 label "-" ]
		edge [ source 2 target 3 label "-" ]
		edge [ source 2 target 4 label "-" ]
		edge [ source 5 target 6 label "=" ]
		edge [ source 5 target 7 label "-" ]
	]
	constrainAdj [
		id 1
		op "="
		count 0
		edgeLabels [ label "=" label "#" label ":" ]
	]
]