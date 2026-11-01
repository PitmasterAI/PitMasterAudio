package es.pitmasterai.masterlab.motor;

import es.pitmasterai.masterlab.motor.Compresor;

public final class Preset {
    public final String clave;
    public final Compresor.Ajuste compAlto;
    public final Compresor.Ajuste compBajo;
    public final Compresor.Ajuste compMedio;
    public final float compScale;
    public final float crossAlto;
    public final float crossBajo;
    public final double[] eqFreqs;
    public final double[] eqGains;
    public final float hpfHz;
    public final float lookaheadMs;
    public final float lufs;
    public final float midDb;
    public final float releaseMs;
    public final float reverbWet;
    public final float satDrive;
    public final float satEven;
    public final float satMix;
    public final float satTone;
    public final float sideDb;
    public final float techoDb;

    public Preset(String str, double[] dArr, double[] dArr2, float f, float f2, float f3, float f4, Compresor.Ajuste ajuste, Compresor.Ajuste ajuste2, Compresor.Ajuste ajuste3, float f5, float f6, float f7, float f8, float f9, float f10, float f11, float f12, float f13, float f14, float f15) {
        this.clave = str;
        this.eqFreqs = dArr;
        this.eqGains = dArr2;
        this.hpfHz = f;
        this.compScale = f2;
        this.crossBajo = f3;
        this.crossAlto = f4;
        this.compBajo = ajuste;
        this.compMedio = ajuste2;
        this.compAlto = ajuste3;
        this.satDrive = f5;
        this.satMix = f6;
        this.satEven = f7;
        this.satTone = f8;
        this.sideDb = f9;
        this.midDb = f10;
        this.reverbWet = f11;
        this.lufs = f12;
        this.techoDb = f13;
        this.lookaheadMs = f14;
        this.releaseMs = f15;
    }
}
