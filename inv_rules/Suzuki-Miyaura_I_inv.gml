rule [
	labelType "term"
	left [
		edge [ source 3 target 5 label "-" ]
		edge [ source 4 target 6 label "-" ]
	]
	context [
		node [ id 1 label "O" ]
		node [ id 2 label "O" ]
		node [ id 3 label "B" ]
		node [ id 4 label "C" ]
		node [ id 5 label "I" ]
		node [ id 6 label "C" ]
		edge [ source 2 target 3 label "-" ]
		edge [ source 1 target 3 label "-" ]
	]
	right [
		edge [ source 3 target 4 label "-" ]
		edge [ source 5 target 6 label "-" ]
	]
	constrainAdj [
		id 4
		op ">="
		count 1
		edgeLabels [ label ":" label "=" label "#" ]
	]
	constrainAdj [
		id 6
		op ">="
		count 1
		edgeLabels [ label ":" label "=" label "#" ]
	]
]