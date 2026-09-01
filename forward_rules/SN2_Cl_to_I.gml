rule [
	ruleID "r_{0}, inverse"
	labelType "term"
	left [
		node [ id 1 label "Cl" ]
		node [ id 2 label "I-" ]
		edge [ source 0 target 1 label "-" ]
	]
	context [
		node [ id 0 label "C" ]
	]
	right [
		node [ id 1 label "Cl-" ]
		node [ id 2 label "I" ]
		edge [ source 0 target 2 label "-" ]
	]
]