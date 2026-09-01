rule [
	ruleID "r_{38}, inverse"
	labelType "term"
	left [
		node [ id 3 label "N-" ]
		node [ id 4 label "N+" ]
		node [ id 5 label "N-" ]
		node [ id 6 label "H+" ]
		edge [ source 1 target 2 label "#" ]
		edge [ source 3 target 4 label "=" ]
		edge [ source 4 target 5 label "=" ]
	]
	context [
		node [ id 0 label "C" ]
		node [ id 1 label "N" ]
		node [ id 2 label "C" ]
		edge [ source 0 target 2 label "-" ]
	]
	right [
		node [ id 3 label "N" ]
		node [ id 4 label "N" ]
		node [ id 5 label "N" ]
		node [ id 6 label "H" ]
		edge [ source 1 target 2 label ":" ]
		edge [ source 1 target 5 label ":" ]
		edge [ source 2 target 3 label ":" ]
		edge [ source 3 target 4 label ":" ]
		edge [ source 4 target 5 label ":" ]
		edge [ source 5 target 6 label "-" ]
	]
]