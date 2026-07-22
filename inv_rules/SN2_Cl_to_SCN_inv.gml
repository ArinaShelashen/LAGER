rule [
	left [
		node [ id 12 label "S" ]
		node [ id 9 label "Cl-" ]
		edge [ source 4 target 12 label "-" ]
	]
	context [
		node [ id 4 label "C" ]
		node [ id 13 label "C" ]
		node [ id 14 label "N" ]
		edge [ source 12 target 13 label "-" ]
		edge [ source 13 target 14 label "#" ]
	]
	right [
		node [ id 12 label "S-" ]
		node [ id 9 label "Cl" ]
		edge [ source 4 target 9 label "-" ]
	]
	constrainAdj [
		id 4
		op "="
		count 0
		edgeLabels [ label ":" label "=" label "#" ]
	]
]