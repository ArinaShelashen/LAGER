rule [
	labelType "term"
	left [
		edge [ source 5 target 2 label "-" ]
		edge [ source 4 target 2 label "-" ]
		edge [ source 6 target 1 label "-" ]
		edge [ source 7 target 1 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "O" ]
		node [ id 3 label "N" ]
		node [ id 4 label "H" ]
		node [ id 5 label "H" ]
		node [ id 6 label "H" ]
		node [ id 7 label "H" ]
		edge [ source 1 target 3 label "-" ]
	]
	right [
		edge [ source 6 target 7 label "-" ]
		edge [ source 4 target 5 label "-" ]
		edge [ source 2 target 1 label "=" ]
	]
	constrainAdj [
		id 3
		op "="
		count 3
		nodeLabels [ label "C" label "H" ]
	]
	constrainAdj [
		id 1
		op "="
		count 3
		nodeLabels [ label "C" label "H" ]
	]
]