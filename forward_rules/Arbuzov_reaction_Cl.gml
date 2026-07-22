rule [
	left [
		edge [ source 9 target 10 label "-" ]
		edge [ source 10 target 11 label "-" ]
		edge [ source 3 target 1 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 3 label "Cl" ]
		node [ id 9 label "P" ]
		node [ id 10 label "O" ]
		node [ id 11 label "C" ]
		node [ id 14 label "O" ]
		node [ id 15 label "C" ]
		edge [ source 14 target 9 label "-" ]
		edge [ source 15 target 14 label "-" ]
	]
	right [
		edge [ source 9 target 10 label "=" ]
		edge [ source 1 target 9 label "-" ]
		edge [ source 11 target 3 label "-" ]
	]
	constrainAdj [
		id 1
		op "="
		count 0
		edgeLabels [ label ":" label "=" label "#" ]
	]
	constrainAdj [
		id 11
		op "="
		count 0
		edgeLabels [ label ":" label "=" label "#" ]
	]
	constrainAdj [
		id 11
		op "<="
		count 1
		nodeLabels [ label "C" ]
	]
]