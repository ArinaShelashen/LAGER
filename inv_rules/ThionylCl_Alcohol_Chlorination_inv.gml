rule [
	labelType "term"
	left [
		edge [ source 1 target 2 label "-" ]
		edge [ source 3 target 6 label "=" ]
		edge [ source 4 target 8 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "Cl" ]
		node [ id 3 label "O" ]
		node [ id 4 label "H" ]
		node [ id 6 label "S" ]
		node [ id 7 label "O" ]
		node [ id 8 label "Cl" ]
		edge [ source 6 target 7 label "=" ]
	]
	right [
		edge [ source 1 target 3 label "-" ]
		edge [ source 6 target 2 label "-" ]
		edge [ source 6 target 8 label "-" ]
		edge [ source 3 target 4 label "-" ]
	]
	constrainAdj [
		id 1
		op "="
		count 0
		edgeLabels [ label ":" label "=" label "#" ]
	]
]