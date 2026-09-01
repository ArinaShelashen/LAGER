rule [
	labelType "term"
	left [
		edge [ source 2 target 4 label ":" ]
		edge [ source 1 target 2 label ":" ]
		edge [ source 3 target 6 label "-" ]
		edge [ source 4 target 5 label ":" ]
		edge [ source 3 target 1 label ":" ]
		edge [ source 5 target 3 label ":" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "C" ]
		node [ id 3 label "N" ]
		node [ id 4 label "N" ]
		node [ id 5 label "N" ]
		node [ id 6 label "H" ]
	]
	right [
		edge [ source 2 target 4 label "=" ]
		edge [ source 1 target 2 label "-" ]
		edge [ source 5 target 6 label "-" ]
		edge [ source 4 target 5 label "-" ]
		edge [ source 3 target 1 label "=" ]
		edge [ source 5 target 3 label "-" ]
	]
]