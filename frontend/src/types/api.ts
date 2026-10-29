export type QueryField = {value:string;basis:string;certainty:string}
export type EmotionDetection = {method:string;model_name:string;primary:string;secondary:string[];confidence:number|string;confidence_label:string;alternative_scores:Record<string,number>;fallback_reason:string}
export type Interpretation = {emotion_detection:EmotionDetection;emotion:QueryField;contextual_interpretation:QueryField;situation:QueryField;relationship:QueryField;domain:QueryField;tinai:QueryField;uri:QueryField;routing_uri:QueryField;prototype_notice:string}
export type Result = {rank:number;score:number;score_type:string;explanation:string;relevance_note:string;poem_id:string;poem_number:string;poem_text:string;akam_puram:string;tinai:string;uri:string;emotion:string;situation:string;characters:string;keywords:string;source:string;source_url:string;annotation_notes:string;annotation_status:string}
export type SearchResponse = {model:string;query:string;context:string[];interpretation:Interpretation;no_strong_match:boolean;results:Result[]}
export type Stats = {records:number;emotion:number;situation:number;characters:number;keywords:number;uri:number;reviewed:number;draft:number;needs_review:number;validated:number;source:string;notes:string}
export type PilotQuery = {query_id:string;modern_situation:string;candidate_poem_ids:string;review_status:string;notes:string}
