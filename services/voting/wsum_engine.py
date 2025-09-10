import math
from models.types import VoteReq, VoteResp, VoteExplain

def vote_to_score(v: str) -> int:
    return 1 if v=='BUY' else (-1 if v=='SELL' else 0)

class WSUMEngine:
    def vote(self, req: VoteReq) -> VoteResp:
        s=0.0; weights={}
        for p in req.proposals:
            s += p.weight * vote_to_score(p.vote)
            weights[p.agent] = p.weight
        decision = 'BUY' if s>0.05 else ('SELL' if s<-0.05 else 'HOLD')
        prob_up = 1.0/(1.0+math.exp(-3.0*s))
        explain = VoteExplain(weights=weights, meta={'method':'WSUM','thresholds':'+/-0.05'})
        return VoteResp(decision=decision, explain=explain, calibrated_probs={'up_48h': round(prob_up,3), 'down_48h': round(1-prob_up,3)})
