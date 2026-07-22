rule [
	left [
		node [ id 11 label "C-" ]
		node [ id 3 label "Br" ]
		edge [ source 3 target 1 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 10 label "N" ]
		edge [ source 10 target 11 label "#" ]
	]
	right [
		node [ id 11 label "C" ]
		node [ id 3 label "Br-" ]
		edge [ source 11 target 1 label "-" ]
	]
	constrainAdj [
		id 1
		op "="
		count 0
		edgeLabels [ label ":" label "=" label "#" ]
	]
]