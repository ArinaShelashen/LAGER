rule [
	labelType "term"
	left [
		edge [ source 1 target 2 label "-" ]
		edge [ source 4 target 3 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "Cl" ]
		node [ id 3 label "N" ]
		node [ id 4 label "H" ]
		node [ id 5 label "H" ]
		node [ id 6 label "C" ]
		edge [ source 3 target 5 label "-" ]
		edge [ source 3 target 6 label "-" ]
	]
	right [
		edge [ source 2 target 4 label "-" ]
		edge [ source 1 target 3 label "-" ]
	]
	constrainAdj [
		id 1
		op ">="
		count 1
		nodeLabels [  ]
		edgeLabels [ label ":" label "=" ]
	]
	constrainAdj [
		id 6
		op "="
		count 0
		nodeLabels [ label "O" label "N" label "S" label "Cl" label "Br" label "F" label "I" ]
		edgeLabels [ label "-" ]
	]
	constrainAdj [
		id 6
		op "="
		count 0
		edgeLabels [ label "=" label "#" ]
	]
]