rule [
	labelType "term"
	left [
		edge [ source 1 target 4 label "-" ]
		edge [ source 2 target 5 label "-" ]
	]
	context [
		node [ id 1 label "N" ]
		node [ id 2 label "H" ]
		node [ id 4 label "C" ]
		node [ id 5 label "Cl" ]
		node [ id 6 label "O" ]
		edge [ source 4 target 6 label "=" ]
	]
	right [
		edge [ source 5 target 4 label "-" ]
		edge [ source 2 target 1 label "-" ]
	]
	constrainAdj [
		id 4
		op "="
		count 1
		nodeLabels [ label "C" label "H" ]
	]
]