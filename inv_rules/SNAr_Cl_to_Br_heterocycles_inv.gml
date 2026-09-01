rule [
	labelType "term"
	left [
		node [ id 1 label "Cl-" ]
		node [ id 3 label "Br" ]
		edge [ source 2 target 3 label "-" ]
	]
	context [
		node [ id 2 label "C" ]
	]
	right [
		node [ id 1 label "Cl" ]
		node [ id 3 label "Br-" ]
		edge [ source 1 target 2 label "-" ]
	]
	constrainAdj [
		id 2
		op ">="
		count 1
		nodeLabels [ label "N" ]
	]
	constrainAdj [
		id 2
		op "="
		count 2
		edgeLabels [ label ":" ]
	]
]