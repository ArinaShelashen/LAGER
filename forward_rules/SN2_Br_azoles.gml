rule [
	left [
		edge [ source 3 target 1 label "-" ]
		edge [ source 10 target 11 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 3 label "Br" ]
		node [ id 11 label "H" ]
		node [ id 10 label "N" ]
	]
	right [
		edge [ source 3 target 11 label "-" ]
		edge [ source 1 target 10 label "-" ]
	]
	constrainAdj [
		id 10
		op ">="
		count 1
		nodeLabels [ label "C" label "N" ]
	]
	constrainAdj [
		id 1
		op "="
		count 0
		edgeLabels [ label ":" label "=" label "#" ]
	]
	constrainAdj [
		id 10
		op ">="
		count 1
		edgeLabels [ label ":" ]
	]
]